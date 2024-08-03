**Description**
This process involves creating a MongoDB Replica on AWS using EC2 instances. The stack assumes the usage of Ubuntu operating systems, as it utilizes the Ubuntu EC2 stacks.

To set up the MongoDB Replica, the following steps are typically followed:

 - Provisioning EC2 Instances: EC2 instances running Ubuntu OS are created on AWS. These instances serve as the virtual machines (VMs) for hosting the MongoDB Replica.

 - Installing MongoDB: MongoDB, the NoSQL database system, is installed on each of the EC2 instances. This involves downloading and configuring MongoDB to run on the Ubuntu OS.

 - Configuring Replica Set: The MongoDB instances are configured to form a replica set. This involves designating one instance as the primary node and the others as secondary nodes. The primary node handles write operations, while the secondary nodes replicate data from the primary node and handle read operations.

 - Establishing Connectivity: The EC2 instances are configured with appropriate security groups and network settings to ensure connectivity between the MongoDB replica set and other components or applications that need to interact with it.

In summary, this process involves creating a MongoDB Replica on AWS using EC2 instances running Ubuntu OS. By configuring a replica set, data can be replicated across multiple instances for improved data availability and fault tolerance.

**Infrastructure**

If the necessary network and other arguments are stored in the Config0 resources database, such as a VPC created using Config0 stacks, users can utilize "selectors" to reference those resources when configuring their setup. However, if the required information is not available in the resources database, users have the option to explicitly input variables like vpc_id, subnet_ids, and security_group_ids for the respective arguments.

It's worth noting that an additional option is available to utilize spot instances. Spot instances are instances that are purchased at a lower price when there is excess capacity in the AWS cloud. However, it's important to exercise caution when using spot instances, as there is a possibility of failure if the spot price is too low or if there is no available capacity at the desired price.

**Required**

| argument      | description                            | var type      | default      |
| ------------- | -------------------------------------- |---------------| ------------ |
| mongodb_cluster   | the name of the mongodb cluster       | string        | None         |
| num_of_replicas   | the number of replicas in the mongodb cluster       | integer       | 1         |
| vpc_id | the vpc id | string        | None       |
| subnet_ids   | a subnet for the VMs is selected from a list of the provided subnet_ids  | string in csv | None         |
| sg_id   | the security group id for the VMs       | string        | None         |
| bastion_subnet_ids   | the subnet_ids to select a subnet_id for the bastion host       | string in csv | None         |
| bastion_sg_id   | the security group id for the bastion host       | string        | None         |

**Optional**

| argument               | description                                                                   | var type | default          |
|------------------------|-------------------------------------------------------------------------------|----------|------------------|
| mongodb_version        | the mongodb version to install                                                | string   | 4.2              |
| config_network         | the network to push configuration to mongodb hosts                            | private/public  | private          |
| spot                   | the option to use spot intances. (buyer be aware)                             | boolean  | None             |
| spot_type              | the option to set spot type for spot instances                                | string   | persistent       |
| spot_max_price         | the option to set spot max price spot instances                               | string   | None             |
| ami                    | the ami image used for mongodb instances                                      | string   | None             |
| ami_filter             | the ami filter used to search for an image as a base for mongodb instances    | string   | None             |
| ami_owner              | the ami owner used to search for an image as a base for mongodb instances     | string   | None             |
| bastion_ami            | the ami image used for the bastion config host                                | string   | None             |
| bastion_ami_filter     | the ami filter used to search for an image as a base for the bastion host     | string   | None             |
| bastion_ami_owner      | the ami owner used to search for an image as a base for the bastion host      | string   | None             |
| aws_default_region     | the aws region                                                                | string   | us-east-1        |
| hostname_random        | generates random hostname base for the VM instances                           | string   | master           |
| bastion_config_destroy | destroys the bastion configuration host after configuration/build is finished | string   | true             |
| instance_type          | the instance_type for the VMs                                                 | string   | t3.micro         |
| disksize               | the disksize for the VM                                                       | string   | None             |
| mongodb_username       | the master mongodb username                                                   | string   | -random-         |
| mongodb_password       | the master mongodb password                                                   | string   | -random-         |
| volume_size            | the volume size for mongodb data                                              | string   | 100              |
| volume_mountpoint      | the volume mountpoint for mongodb data                                        | string   | /var/lib/mongodb |
| volume_fstype          | the volume fileystem type for mongodb data                                    | string   | xfs              |
| tags                   | the tags for the mongodb cluster in the Config0 resources database            | string   | None             |
| labels                 | the labels for the mongodb cluster in the Config0 resources database          | string   | None             |
| cloud_tags_hash | the tags for the resources in the cloud as base64                             | string  | None             |
| publish_to_saas   | publish info of db to Config0 UI                                              | boolean   | True             |



**Sample entry**
```
global:
   arguments:
     aws_default_region: eu-west-1
     cloud_tags_hash:
       environment: dev
       purpose: eval-config0
       database: mongodb
       product: ec2
       database_type: nosql
labels:
   general:
     environment: dev
     purpose: eval-config0
   infrastructure:
     cloud: aws
     product: mongodb
selectors:
   network_vars:
     labels:
       environment: dev
       purpose: eval-config0
       area: network
       region: eu-west-1
       cloud: aws
infrastructure:
   mongodb_replica:
     stack_name: config0-publish:::mongodb_replica_on_ec2
     arguments:
        vpc_name: selector:::network_vars::vpc_name
        vpc_id: selector:::network_vars::vpc_id
        subnet_ids: selector:::network_vars::public_subnet_ids
        sg_id: selector:::network_vars::db_sg_id
        bastion_sg_id: selector:::network_vars::bastion_sg_id
        bastion_subnet_ids: selector:::network_vars::public_subnet_ids
        mongodb_cluster: mongodb-cluster-dev
        ami_filter: ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-*
        ami_owner: 099720109477
        bastion_ami_filter: ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-*
        bastion_ami_owner: 099720109477
        instance_type: t3.micro
        spot: true
        num_of_replicas: 3
        disksize: 25
        volume_size: 25
        volume_mount: /var/lib/mongodb
        volume_fstype: xfs
        mongodb_username: admin123
        mongodb_password: admin123
        publish_to_saas: true
     to_base64:
       - cloud_tags_hash
     selectors:
       - network_vars
     credentials:
       - reference: eval-config0-iam
         orchestration: true
```
