
class Main(newSchedStack):

    def __init__(self, stackargs):

        newSchedStack.__init__(self, stackargs)

        # Add default variables
        self.parse.add_required(key="ci_environment")

        # this is required to make the buckets unique
        self.parse.add_optional(key="suffix_id",
                                types="str")

        self.parse.add_optional(key="suffix_length",
                                types="int",
                                default="4")

        self.parse.add_optional(key="aws_default_region",
                                types="str",
                                default="eu-west-1")

        self.parse.add_optional(key="cloud_tags_hash",
                                types="str")

        self.parse.add_optional(key="bucket_acl",
                                types="str",
                                default="private")

        self.parse.add_optional(key="bucket_expire_days",
                                types="int",
                                default="7")

        self.parse.add_optional(key="runtime",
                                types="str",
                                default="python3.9")

        self.parse.add_optional(key="lambda_layers",
                                types="str",
                                default="arn:aws:lambda:eu-west-1:553035198032:layer:git-lambda2:8")

        # Add substack
        self.stack.add_substack("config0-publish:::aws_s3_bucket")
        self.stack.add_substack("config0-publish:::aws_dynamodb")
        self.stack.add_substack("config0-publish:::aws-lambda-python-codebuild","py_lambda")
        self.stack.add_substack("config0-publish:::apigw_lambda-integ","apigw")
        self.stack.add_substack("config0-publish:::codebuild_stepf_ci")
        self.stack.add_substack("config0-publish:::codebuild_complete_trigger",
                                "sns_subscription")

        # this is lock versioning of execgroups
        self.stack.add_execgroup("config0-publish:::github::lambda_trigger_stepf")
        self.stack.add_execgroup("config0-publish:::github::lambda_codebuild")
        self.stack.add_execgroup("config0-publish:::github::lambda_check_codebuild")
        self.stack.add_execgroup("config0-publish:::github::lambda_s3")
        self.stack.add_execgroup("config0-publish:::github::lambda_webhook")

        self.stack.init_execgroups()
        self.stack.init_substacks()

    def _determine_suffix_id(self):

        if self.stack.get_attr("suffix_id"):
            return str(self.stack.suffix_id).lower()

        return self.stack.b64_encode(self.stack.ci_environment)[0:int(self.stack.suffix_length)].lower()

    def _set_cloud_tag_hash(self):

        try:
            cloud_tags = self.stack.b64_decode(self.stack.cloud_tags_hash)
        except:
            cloud_tags = {}

        cloud_tags.update({
            "ci_environment": self.stack.ci_environment,
            "aws_default_region": self.stack.aws_default_region
        })

        return self.stack.b64_encode(cloud_tags)

    def _get_env_vars_lambda_hashes(self):

        base_hash = self.stack.b64_encode({"ENV": "build"})

        # this setting is for
        # processing the webhook
        env_vars = {
            "ENV": "build",
            "DEBUG_LAMBDA": "true",
            "BUILD_TTL": "60",
            "DISABLE_BRANCH_CHECK": "false",
            "DISABLE_EVENT_CHECK": "false"
        }

        webhook_hash = self.stack.b64_encode(env_vars)

        return base_hash, webhook_hash

    def _s3(self,cloud_tags_hash):

        suffix_id = self._determine_suffix_id()

        if "_" in self.stack.ci_environment:
            msg = "Cannot use underscores (Only hyphens) in the ci_environment"
            raise Exception(msg)

        # perm shared bucket
        s3_bucket = "codebuild-shared-{}-{}".format(self.stack.ci_environment,
                                                    suffix_id)

        arguments = {
            "bucket": s3_bucket,
            "acl": self.stack.bucket_acl,
            "cloud_tags_hash": cloud_tags_hash,
            "force_destroy": "true",
            "enable_lifecycle": "false",
            "aws_default_region": self.stack.aws_default_region
        }

        human_description= "Create s3 bucket {}".format(s3_bucket)
        inputargs = {
            "arguments": arguments,
            "automation_phase": "infrastructure",
            "human_description": human_description
        }

        self.stack.aws_s3_bucket.insert(display=True, 
                                        **inputargs)

        # temp shared bucket
        s3_bucket = "codebuild-shared-{}-{}-tmp".format(self.stack.ci_environment,
                                                        suffix_id)

        arguments = {
            "bucket": s3_bucket,
            "acl": self.stack.bucket_acl,
            "cloud_tags_hash": cloud_tags_hash,
            "expire_days": self.stack.bucket_expire_days,
            "force_destroy": "true",
            "enable_lifecycle": "true",
            "aws_default_region": self.stack.aws_default_region
        }

        human_description= "Create s3 bucket {}".format(s3_bucket)
        inputargs = {
            "arguments": arguments,
            "automation_phase": "infrastructure",
            "human_description": human_description
        }

        self.stack.aws_s3_bucket.insert(display=True,
                                         **inputargs)

    def _dynamodb(self,cloud_tags_hash):

        for suffix in ["runs", "settings"]:

            dynamodb_name = "codebuild-shared-{}-{}".format(self.stack.ci_environment,
                                                            suffix)

            arguments = {
                "dynamodb_name": dynamodb_name,
                "cloud_tags_hash": cloud_tags_hash,
                "aws_default_region": self.stack.aws_default_region
            }

            human_description= "Create dynamodb {}".format(dynamodb_name)
            inputargs = {
                "arguments": arguments,
                "automation_phase": "infrastructure",
                "human_description": human_description
            }

            self.stack.aws_dynamodb.insert(display=True, **inputargs)

    def _get_log_policy(self):

        _statement = {
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*",
            "Effect": "Allow"
        }

        return _statement

    def _get_dynamodb_policy(self):

        dynamodb_name_runs = "codebuild-shared-{}-{}".format(
            self.stack.ci_environment, "runs")

        dynamodb_name_settings = "codebuild-shared-{}-{}".format(
            self.stack.ci_environment, "settings")

        arn_dynamodb_name_runs = "arn:aws:dynamodb:{}:".format(
            self.stack.aws_default_region) + '${aws_account_id}:table/' + dynamodb_name_runs

        arn_dynamodb_name_settings = "arn:aws:dynamodb:{}:".format(
            self.stack.aws_default_region) + '${aws_account_id}:table/' + dynamodb_name_settings

        _statement = {
            "Effect": "Allow",
            "Action": ["dynamodb:DescribeTable",
                       "dynamodb:PartiQLInsert",
                       "dynamodb:GetItem",
                       "dynamodb:BatchGetItem",
                       "dynamodb:BatchWriteItem",
                       "dynamodb:UpdateTimeToLive",
                       "dynamodb:PutItem",
                       "dynamodb:PartiQLUpdate",
                       "dynamodb:Scan",
                       "dynamodb:UpdateItem",
                       "dynamodb:UpdateTable",
                       "dynamodb:GetRecords",
                       "dynamodb:ListTables",
                       "dynamodb:DeleteItem",
                       "dynamodb:ListTagsOfResource",
                       "dynamodb:PartiQLSelect",
                       "dynamodb:ConditionCheckItem",
                       "dynamodb:Query",
                       "dynamodb:DescribeTimeToLive",
                       "dynamodb:ListStreams",
                       "dynamodb:PartiQLDelete"
                       ],
            "Resource": [ arn_dynamodb_name_runs, 
                          arn_dynamodb_name_settings ]
        }

        return _statement

    def _get_s3_policies(self):

        statements = []
        s3_bucket = self._get_s3_bucket()

        arn_s3_bucket = "arn:aws:s3:::{}".format(s3_bucket)
        arn_s3_bucket_tmp = "arn:aws:s3:::{}-tmp".format(s3_bucket)

        _statement = {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": [arn_s3_bucket,
                         arn_s3_bucket_tmp,
                         "{}/*".format(arn_s3_bucket),
                         "{}/*".format(arn_s3_bucket_tmp)]
        }

        statements.append(_statement)

        _statement = {
            "Effect": "Allow",
            "Action": [
                "s3:ListAllMyBuckets",
                "ssm:*"
            ],
            "Resource": "*"
        }

        statements.append(_statement)

        return statements

    def _get_lambda_policy(self):

        _action = ["lambda:TagResource",
                   "lambda:GetFunctionConfiguration",
                   "lambda:ListProvisionedConcurrencyConfigs",
                   "lambda:GetProvisionedConcurrencyConfig",
                   "lambda:ListLayerVersions",
                   "lambda:ListLayers",
                   "lambda:ListCodeSigningConfigs",
                   "lambda:GetAlias",
                   "lambda:ListFunctions",
                   "lambda:GetEventSourceMapping",
                   "lambda:InvokeFunction",
                   "lambda:ListAliases",
                   "lambda:GetFunctionCodeSigningConfig",
                   "lambda:ListFunctionEventInvokeConfigs",
                   "lambda:ListFunctionsByCodeSigningConfig",
                   "lambda:GetFunctionConcurrency",
                   "lambda:ListEventSourceMappings",
                   "lambda:ListVersionsByFunction",
                   "lambda:GetLayerVersion",
                   "lambda:InvokeAsync",
                   "lambda:GetAccountSettings",
                   "lambda:GetLayerVersionPolicy",
                   "lambda:UntagResource",
                   "lambda:ListTags",
                   "lambda:GetFunction",
                   "lambda:GetFunctionEventInvokeConfig",
                   "lambda:GetCodeSigningConfig",
                   "lambda:GetPolicy"]

        _statement = {"Action": _action,
                      "Resource": "*",
                      "Effect": "Allow"
                      }

        return _statement

    def _get_codebuild_policy(self):

        _action = ["codebuild:ListReportsForReportGroup",
                   "codebuild:ListBuildsForProject",
                   "codebuild:BatchGetBuilds",
                   "codebuild:StopBuildBatch",
                   "codebuild:ListReports",
                   "codebuild:DeleteBuildBatch",
                   "codebuild:BatchGetReports",
                   "codebuild:ListCuratedEnvironmentImages",
                   "codebuild:ListBuildBatches",
                   "codebuild:ListBuilds",
                   "codebuild:BatchDeleteBuilds",
                   "codebuild:StartBuild",
                   "codebuild:BatchGetBuildBatches",
                   "codebuild:GetResourcePolicy",
                   "codebuild:StopBuild",
                   "codebuild:RetryBuild",
                   "codebuild:ImportSourceCredentials",
                   "codebuild:BatchGetReportGroups",
                   "codebuild:BatchGetProjects",
                   "codebuild:RetryBuildBatch",
                   "codebuild:StartBuildBatch"]

        _statement = {"Action": _action,
                      "Resource": "*",
                      "Effect": "Allow"
                      }

        return _statement

    def _get_stepf_policy(self):
        
        _action = [
            "states:StartExecution",
            "states:StopExecution",
            "states:DescribeExecution",
            "states:ListExecutions",
            "states:DescribeStateMachine",
            "states:GetExecutionHistory"
        ]

        _statement = {"Action": _action,
                      "Resource": "*",
                      "Effect": "Allow"
                      }

        return _statement

    def _get_policy_template_hash(self):

        statements = []

        _statement = {"Action": ["ssm:*"],
                      "Resource": "*",
                      "Effect": "Allow"
                      }

        statements.append(_statement)
        statements.append(self._get_log_policy())
        statements.append(self._get_dynamodb_policy())
        statements.extend(self._get_s3_policies())
        statements.append(self._get_lambda_policy())
        statements.append(self._get_codebuild_policy())

        policy = {"Version": "2012-10-17",
                  "Statement": statements}

        return self.stack.b64_encode(policy,
                                     json_dumps=True)

    def _get_stepf_policy_template_hash(self):

        statements = [self._get_log_policy()]
        statements.extend(self._get_s3_policies())
        statements.append(self._get_lambda_policy())
        statements.append(self._get_stepf_policy())

        policy = {"Version": "2012-10-17",
                  "Statement": statements}

        return self.stack.b64_encode(policy,
                                     json_dumps=True)

    def _get_s3_bucket(self):

        suffix_id = self._determine_suffix_id()
        s3_bucket = "codebuild-shared-{}-{}".format(
            self.stack.ci_environment, suffix_id)

        return s3_bucket

    def _get_stepf_name(self):
         return "{}-codebuild-stepf-ci".format(self.stack.ci_environment)

    def _get_stepf_arn(self):

        stepf_name = self._get_stepf_name()

        _info = self.stack.get_resource(name=stepf_name,
                                        resource_type="step_function",
                                        must_be_one=True)[0]

        return _info["arn"]

    def _stepf(self,cloud_tags_hash):

        stepf_name = self._get_stepf_name()

        arguments = {
            "step_function_name": stepf_name,
            "cloud_tags_hash": cloud_tags_hash,
            "aws_default_region": self.stack.aws_default_region
        }

        human_description = "Create step function {}".format(stepf_name)

        inputargs = {
            "arguments": arguments,
            "automation_phase": "infrastructure",
            "human_description": human_description
        }

        self.stack.codebuild_stepf_ci.insert(display=True,
                                                 **inputargs)

        return

    def _lambda(self,cloud_tags_hash):

        self.stack.set_parallel()

        s3_bucket = self._get_s3_bucket()
        policy_template_hash = self._get_policy_template_hash()
        base_env_vars_hash, webhook_env_vars_hash = self._get_env_vars_lambda_hashes()

        base_arguments = {
            "s3_bucket": s3_bucket,
            "runtime": self.stack.runtime,
            "policy_template_hash": policy_template_hash,
            "lambda_env_vars_hash": base_env_vars_hash,
            "cloud_tags_hash": cloud_tags_hash,
            "aws_default_region": self.stack.aws_default_region
        }

        if self.stack.lambda_layers:
            base_arguments["lambda_layers"] = self.stack.lambda_layers

        # lambda_name = "process-webhook"
        lambda_name = "process-webhook"
        handler = "app_webhook.handler"
        s3_key = "{}.zip".format(lambda_name)

        arguments = base_arguments.copy()
        arguments.update({
            "lambda_env_vars_hash": webhook_env_vars_hash,   # this is special for the processing of the webhook
            "lambda_name": lambda_name,
            "handler": handler,
            "s3_key": s3_key,
            "config0_lambda_execgroup_name": self.stack.lambda_webhook.name})

        human_description= "Create lambda function {}".format(lambda_name)
        inputargs = {"arguments": arguments,
                     "automation_phase": "infrastructure",
                     "human_description": human_description}

        self.stack.py_lambda.insert(display=True,
                                    **inputargs)

        lambda_params = { "trigger-codebuild":["app_codebuild.handler",
                                               self.stack.lambda_codebuild.name],
                          "pkgcode-to-s3":["app_s3.handler",
                                           self.stack.lambda_s3.name],
                          "check-codebuild":["app_check_build.handler",
                                             self.stack.lambda_check_codebuild.name]
                          }

        for lambda_name, params in lambda_params.items():

            arguments = base_arguments.copy()
            arguments.update({
                "lambda_name": lambda_name,
                "handler": params[0],
                "s3_key": "{}.zip".format(lambda_name),
                "config0_lambda_execgroup_name": params[1]
            })

            human_description= 'Create lambda function {}'.format(lambda_name)
            inputargs = {"arguments": arguments,
                         "automation_phase": "infrastructure",
                         "human_description": human_description}

            self.stack.py_lambda.insert(display=True,
                                        **inputargs)

        self.stack.unset_parallel()

    # job definitions are prefixed with run_
    def run_setup(self):

        self.stack.init_variables()
        self.stack.verify_variables()
        cloud_tags_hash = self._set_cloud_tag_hash()

        # set parallel
        self.stack.set_parallel()

        # create s3 buckets
        self._s3(cloud_tags_hash)

        # create dynamodb table
        self._dynamodb(cloud_tags_hash)

        return True

    def run_lambda_stepf(self):

        self.stack.init_variables()
        self.stack.verify_variables()
        cloud_tags_hash = self._set_cloud_tag_hash()

        self.stack.unset_parallel()

        # create lambda functions
        self._lambda(cloud_tags_hash)

        # create step function after lambda funcs
        self._stepf(cloud_tags_hash)

        return True

    def run_trigger_stepf(self):

        self.stack.init_variables()
        self.stack.verify_variables()
        cloud_tags_hash = self._set_cloud_tag_hash()

        s3_bucket = self._get_s3_bucket()
        stepf_arn = self._get_stepf_arn()

        arguments = {
            "s3_bucket": s3_bucket,
            "runtime": self.stack.runtime,
            "policy_template_hash": self._get_stepf_policy_template_hash(),
            "lambda_env_vars_hash": self.stack.b64_encode({"STATE_MACHINE_ARN":stepf_arn}),
            "cloud_tags_hash": cloud_tags_hash,
            "aws_default_region": self.stack.aws_default_region
        }

        if self.stack.lambda_layers:
            arguments["lambda_layers"] = self.stack.lambda_layers

        # lambda_name = "lambda_trigger_stepf"
        lambda_name = "lambda_trigger_stepf"
        handler = "app.handler"
        s3_key = "{}.zip".format(lambda_name)

        arguments.update({
            "lambda_name": lambda_name,
            "handler": handler,
            "s3_key": s3_key,
            "config0_lambda_execgroup_name": self.stack.lambda_trigger_stepf.name})

        human_description= "Create lambda function {}".format(lambda_name)
        inputargs = {"arguments": arguments,
                     "automation_phase": "infrastructure",
                     "human_description": human_description}

        self.stack.py_lambda.insert(display=True,
                                    **inputargs)

    def run_apigw(self):

        self.stack.init_variables()
        self.stack.verify_variables()

        cloud_tags_hash = self._set_cloud_tag_hash()

        apigateway_name = "config0-codebuild-shared-{}".format(
            self.stack.ci_environment)

        # will trigger the lambda function
        # that will trigger the step function
        lambda_name = "lambda_trigger_stepf"

        arguments = {
            "apigateway_name": apigateway_name,
            "cloud_tags_hash": cloud_tags_hash,
            "lambda_name": lambda_name,
            "aws_default_region": self.stack.aws_default_region
        }

        human_description= 'Create API gateway {}'.format(apigateway_name)
        inputargs = {
            "arguments": arguments,
            "automation_phase": "infrastructure",
            "human_description": human_description
        }

        return self.stack.apigw.insert(display=True,
                                       **inputargs)

    def run_sns_subscription(self):

        self.stack.init_variables()
        self.stack.verify_variables()

        lambda_name = "check-codebuild"
        topic_name = "{}-codebuild-compelete-trigger".format(
            self.stack.ci_environment)

        cloud_tags_hash = self._set_cloud_tag_hash()

        arguments = {"lambda_name": lambda_name,
                     "cloud_tags_hash": cloud_tags_hash,
                     "topic_name": topic_name,
                     "aws_default_region": self.stack.aws_default_region}

        human_description = "Create Codebuild SNS subscription for {}".format(self.stack.ci_environment)
        inputargs = {"arguments": arguments,
                     "automation_phase": "infrastructure",
                     "human_description": human_description}

        return self.stack.sns_subscription.insert(display=True, 
                                                  **inputargs)

    def run(self):

        self.stack.unset_parallel(sched_init=True)
        self.add_job("setup")
        self.add_job("lambda_stepf")
        self.add_job("trigger_stepf")
        self.add_job("apigw")
        self.add_job("sns_subscription")

        return self.finalize_jobs()

    def schedule(self):

        sched = self.new_schedule()
        sched.job = "setup"
        sched.archive.timeout = 1800
        sched.archive.timewait = 120
        sched.automation_phase = "infrastructure"
        sched.human_description = "Setup s3 and dynamodb"
        sched.conditions.retries = 1
        sched.on_success = ["lambda_stepf"]
        self.add_schedule()

        sched = self.new_schedule()
        sched.job = "lambda_stepf"
        sched.archive.timeout = 1800
        sched.archive.timewait = 120
        sched.automation_phase = "infrastructure"
        sched.human_description = "Setup lambdas and stepf"
        sched.on_success = ["trigger_stepf"]
        self.add_schedule()

        sched = self.new_schedule()
        sched.job = "trigger_stepf"
        sched.archive.timeout = 1200
        sched.archive.timewait = 120
        sched.automation_phase = "infrastructure"
        sched.human_description = 'Create Lambda Trigger Step function'
        sched.on_success = ["apigw"]
        self.add_schedule()

        sched = self.new_schedule()
        sched.job = "apigw"
        sched.archive.timeout = 1200
        sched.archive.timewait = 120
        sched.automation_phase = "infrastructure"
        sched.human_description = 'Create apigateway'
        sched.on_success = ["sns_subscription"]
        self.add_schedule()

        sched = self.new_schedule()
        sched.job = "sns_subscription"
        sched.archive.timeout = 1200
        sched.archive.timewait = 120
        sched.automation_phase = "infrastructure"
        sched.human_description = 'Create Codebuild Complete Trigger'
        self.add_schedule()

        return self.get_schedules()
