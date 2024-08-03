**Description**
  - The Codebuild CI is expected to be built with stack: 
     - __config0-publish:::setup_codebuild_ci__
    
  - This stack connects a repository for Codebuild CI to be triggered to build on

**Required**

| argument       | description                                                                  | var type | default      |
|----------------|------------------------------------------------------------------------------| -------- | ------------ |
| ci_environment    | environment name for the project                                          | string   | None         |
| codebuild_name    | codebuild name for the project                                            | string   | None         |
| git_repo          | git repository that you want run codebuild ci on                          | string   | None         |
| git_url           | git repository link                                                       | string   | None         |
| project_id        | id of your codebuild project                                              | string   | None         |

**Optional**

| argument                   | description                                        | var type |  default  |
| -------------------------- | -------------------------------------------------- | -------- | --------- |
| aws_default_region         | default aws region                                 |string    | us-west-1 |
| branch                     | git branch you are work on                         |string    | master |
| bucket_acl                 | bucket access control list mode                    |string    | private |
| bucket_expire_days         | bucket retention days                              |int       | 1 |
| build_image                | build image for codebuild project                  |string    | aws/codebuild/standard:5.0 |
| build_timeout              | build timeout for codebuild project                |int       | 444 |
| cloud_tags_hash            | the tags for the resources in the cloud as base64  |string    | None |
| compute_type               | compute type for codebuild project                 |string    | BUILD_GENERAL1_SMALL |
| docker_registry            | docker registry to upload images                   |string    | ecr |
| docker_repo_name           | docker repository name                             |string    | None |
| docker_repository_uri      | docker repository uri                              |string    | None |
| docker_token               | docker token                                       |string    | null |
| docker_username            | docker username                                    |string    | None |
| ecr_repo_name              | elastic container registry name                    |string    | None |
| ecr_repository_uri         | elastic container registry repository uri          |string    | None |
| github_token               | github token                                       |string    | null |
| image_type                 | image type for codebuild project                   |string    | LINUX_CONTAINER |
| privileged_mode            | run as root                                        |bool      | true |
| run_title                  | the run title for the Config0 UI                   |string    | codebuild_ci |
| secret                     | the secret for the webhook validation              |string    | _random |
| slack_channel              | name of the slack channel                          |string    | None |
| slack_webhook_hash         | slack channel webhook as base64                    |string    | null |
| suffix_id                  | suffix_id is added like a random string that makes the s3 buckets unique                          |string    | None |
| suffix_length              | the number of characters in suffix_id to use        |int       | 4 |
| trigger_id                 | job trigger id                                     |string    | _random |





yoyo
yoyo
yoyo
yoyo
yoyo
yoyo
yoyo
yoyo
yoyo
yoyo
yoyo
yoyo
yoyo
yoyo
yoyo
yoyo
yoyo
