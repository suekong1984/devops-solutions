**Description**

  - This stack establishes CodeBuild for continuous integration (CI).
  - It offers a similar level of portability and user-friendliness as CircleCI or TravisCI, but operates within your AWS account.

This stack utilizes:

  - API Gateway
  - S3 storage
  - Lambda functions
  - DynamoDB for build and status tracking
  - AWS Systems Manager Parameter Store for managing sensitive information.

**Gotchas**

  - This stack focuses on configuring the foundation for CodeBuild and does not set up specific repositories for building. 
  - To add repositories, use the config0-publish:::add_codebuild_ci stack.

**Required**

| argument       | description                            | var type | default      |
| -------------- | -------------------------------------- | -------- | ------------ |
| ci_environment | environment name for the project   | string   | None         |

**Optional**

| argument            | description                                        | var type | default   |
| ------------------- | -------------------------------------------------- | -------- | --------- |
| aws_default_region  | default aws region                                 |string    | eu-west-1 |
| bucket_acl          | bucket access control list mode                    |string    | private |
| bucket_expire_days  | bucket retention days                              |int       | 7 |
| cloud_tags_hash     | the tags for the resources in the cloud as base64  |string    | None |
| lambda_layers       | lambda amazon resource name                        |string    | arn:aws:lambda:eu-west-1:553035198032:layer:git-lambda2:8 |
| runtime             | lambda function runtime language                   |string    | python3.9 |
| suffix_id                  | suffix_id is added like a random string that makes the s3 buckets unique                          |string    | None |
| suffix_length              | the number of characters in suffix_id to use        |int       | 4 |
