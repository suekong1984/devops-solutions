data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

locals {
  public_subnets = {
    "${var.aws_default_region}a" = "10.10.101.0/24"
    "${var.aws_default_region}b" = "10.10.102.0/24"
  }
  private_subnets = {
    "${var.aws_default_region}a" = "10.10.201.0/24"
    "${var.aws_default_region}b" = "10.10.202.0/24"
  }
}

resource "aws_vpc" "main" {
  cidr_block = "10.10.0.0/16"

  enable_dns_support   = true
  enable_dns_hostnames = true

  lifecycle {
    ignore_changes = [tags]
  }

  tags = merge(
    var.cloud_tags,
    var.vpc_tags,
    {
      Name      = var.vpc_name
      Product   = "vpc"
    },
  )

}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.main.id

  lifecycle {
    ignore_changes = [tags]
  }

  tags = merge(
    var.cloud_tags,
    var.vpc_tags,
    {
      Name      = "${var.vpc_name}-internet-gateway"
      Product   = "internet-gateway"
    },
  )

}

resource "aws_subnet" "public" {
  count      = "${length(local.public_subnets)}"
  cidr_block = "${element(values(local.public_subnets), count.index)}"
  vpc_id     = aws_vpc.main.id

  map_public_ip_on_launch = true
  availability_zone       = "${element(keys(local.public_subnets), count.index)}"

  lifecycle {
    ignore_changes = [tags]
  }

  tags = merge(
      var.cloud_tags,
      var.vpc_tags,
      var.public_subnet_tags,
      {
        Name                        = "${var.vpc_name}-service-public"
        subnet_environment          = "public"
      },
    )

}

resource "aws_subnet" "private" {
  count      = "${length(local.private_subnets)}"
  cidr_block = "${element(values(local.private_subnets), count.index)}"
  vpc_id     = aws_vpc.main.id

  map_public_ip_on_launch = true
  availability_zone       = "${element(keys(local.private_subnets), count.index)}"

  lifecycle {
    ignore_changes = [tags]
  }

  tags = merge(
      var.cloud_tags,
      var.vpc_tags,
      var.private_subnet_tags,
      {
        Name                        = "${var.vpc_name}-service-private"
        subnet_environment          = "private"
      },
    )

}

######################################################################
# Gateway Endpt
######################################################################

resource "aws_vpc_endpoint" "s3" {
  depends_on = [ aws_vpc.main ]
  vpc_id     = aws_vpc.main.id
  service_name = "com.amazonaws.${var.aws_default_region}.s3"
  route_table_ids = [ aws_route_table.private.id, aws_default_route_table.public.id ]
  tags = merge(
    var.cloud_tags,
    {
      Product = "vpc_endpoint"
      Name    = "s3-gw-endpt-${var.vpc_name}"
    },
  )
}

resource "aws_vpc_endpoint" "dynamodb" {
  depends_on = [ aws_vpc.main ]
  vpc_id     = aws_vpc.main.id
  service_name = "com.amazonaws.${var.aws_default_region}.dynamodb"
  route_table_ids = [ aws_route_table.private.id, aws_default_route_table.public.id ]
  tags = merge(
    var.cloud_tags,
    {
      Product = "vpc_endpoint"
      Name    = "dynamodb-gw-endpt-${var.vpc_name}"
    },
  )
}

######################################################################
# Routing
######################################################################

resource "aws_default_route_table" "public" {
  default_route_table_id = "${aws_vpc.main.main_route_table_id}"

  lifecycle {
    ignore_changes = [tags]
  }

  tags = merge(
    var.cloud_tags,
    var.vpc_tags,
    {
      Name      = "${var.vpc_name}-route-public"
      Product   = "route-table"
    },
  )

}

resource "aws_route" "public_internet_gateway" {
  count                  = "${length(local.public_subnets)}"
  route_table_id         = "${aws_default_route_table.public.id}"
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = "${aws_internet_gateway.this.id}"

  timeouts {
    create = "5m"
  }
}

resource "aws_route_table_association" "public" {
  count          = "${length(local.public_subnets)}"
  subnet_id      = "${element(aws_subnet.public.*.id, count.index)}"
  route_table_id = "${aws_default_route_table.public.id}"
}

resource "aws_route_table" "private" {
  vpc_id     = aws_vpc.main.id

  lifecycle {
    ignore_changes = [tags]
  }


  tags = merge(
    var.cloud_tags,
    var.vpc_tags,
    {
      Name      = "${var.vpc_name}-route-private"
      Product   = "route-table"
    },
  )

}

resource "aws_route_table_association" "private" {
  count          = "${length(local.private_subnets)}"
  subnet_id      = "${element(aws_subnet.private.*.id, count.index)}"
  route_table_id = "${aws_route_table.private.id}"
}

######################################################################
# outputs
######################################################################

output "vpc_id" { value = aws_vpc.main.id }
output "vpc_name" { value = aws_vpc.main.tags.Name }
output "vpc" { value = aws_vpc.main.tags.Name }
output "id" { value = aws_vpc.main.id }
output "name" { value = aws_vpc.main.tags.Name }
output "route_table_private_id" { value = aws_route_table.private.id }
output "route_table_public_id" { value = aws_default_route_table.public.id }





