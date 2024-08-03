data "aws_caller_identity" "current" {}

###############################################################
# Variables
###############################################################

variable "aws_default_region" {
  default = "eu-west-1"
}

variable "step_function_name" {
  default = "apigw-codebuild-ci"
}

variable "process_webhook" {
  default = "process-webhook"
}

variable "pkgcode_to_s3" {
  default = "pkgcode-to-s3"
}

variable "check_codebuild" {
  default = "check-codebuild"
}

variable "trigger_codebuild" {
  default = "trigger-codebuild"
}

variable "cloud_tags" {
  description = "additional tags as a map"
  type        = map(string)
  default     = {}
}

###############################################################
# Main
###############################################################

resource "aws_iam_role" "default" {
  name               = "${var.step_function_name}-role"
  assume_role_policy = <<-EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": "sts:AssumeRole",
        "Principal": {
          "Service": "states.amazonaws.com"
        },
        "Effect": "Allow",
        "Sid": "StepFunctionAssumeRole"
      }
    ]
  }
  EOF
}


resource "aws_sfn_state_machine" "sfn_state_machine" {
  name     = var.step_function_name
  role_arn = aws_iam_role.default.arn

  definition = <<EOF
  {
    "Comment": "The state machine processes webhook from code repo, executes codebuild, and checks results",
    "StartAt": "ProcessWebhook",
    "States": {
      "ProcessWebhook": {
        "Type": "Task",
        "Resource": "arn:aws:lambda:eu-west-1:${data.aws_caller_identity.current.account_id}:function:process-webhook",
        "Next": "ChkProcessWebhook"
      },
      "ChkProcessWebhook": {
        "Type": "Choice",
        "Choices": [
          {
            "Variable": "$.continue",
            "BooleanEquals": true,
            "Next": "PkgCodeToS3"
          }
        ],
        "Default": "Done"
      },
      "PkgCodeToS3": {
        "Type": "Task",
        "Resource": "arn:aws:lambda:eu-west-1:${data.aws_caller_identity.current.account_id}:function:pkgcode-to-s3",
        "Next": "ChkPkgCodeToS3",
        "InputPath": "$.body"
      },
      "ChkPkgCodeToS3": {
        "Type": "Choice",
        "Choices": [
          {
            "Variable": "$.continue",
            "BooleanEquals": true,
            "Next": "TriggerCodebuild"
          }
        ],
        "Default": "Done"
      },
      "TriggerCodebuild": {
        "Type": "Task",
        "Resource": "arn:aws:lambda:eu-west-1:${data.aws_caller_identity.current.account_id}:function:trigger-codebuild",
        "Next": "ChkTriggerCodebuild",
        "InputPath": "$.body"
      },
      "ChkTriggerCodebuild": {
        "Type": "Choice",
        "Choices": [
          {
            "Variable": "$.continue",
            "BooleanEquals": true,
            "Next": "WaitCodebuildCheck"
          }
        ],
        "Default": "Done"
      },
      "WaitCodebuildCheck": {
        "Type": "Wait",
        "Seconds": 30,
        "Next": "CheckCodebuild",
        "Comment": "Wait to Check CodeBuild completion"
      },
      "CheckCodebuild": {
        "Type": "Task",
        "Resource": "arn:aws:lambda:eu-west-1:${data.aws_caller_identity.current.account_id}:function:check-codebuild",
        "Next": "ChkCheckCodebuild",
        "InputPath": "$.body"
      },
      "ChkCheckCodebuild": {
        "Type": "Choice",
        "Choices": [
          {
            "Variable": "$.continue",
            "BooleanEquals": true,
            "Next": "CheckCodebuild"
          }
        ],
        "Default": "Done"
      },
      "Done": {
        "Type": "Pass",
        "End": true
      }
    }
  }
  EOF
}

resource "aws_iam_role_policy" "step_function_policy" {
  name    = "${var.step_function_name}-policy"
  role    = aws_iam_role.default.id

  policy  = <<-EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": [
          "lambda:InvokeFunction"
        ],
        "Effect": "Allow",
        "Resource": [ "arn:aws:lambda:${var.aws_default_region}:${data.aws_caller_identity.current.account_id}:function:${var.process_webhook}",
                      "arn:aws:lambda:${var.aws_default_region}:${data.aws_caller_identity.current.account_id}:function:${var.pkgcode_to_s3}",
                      "arn:aws:lambda:${var.aws_default_region}:${data.aws_caller_identity.current.account_id}:function:${var.trigger_codebuild}",
                      "arn:aws:lambda:${var.aws_default_region}:${data.aws_caller_identity.current.account_id}:function:${var.check_codebuild}" ]
      }
    ]
  }
  EOF
}
