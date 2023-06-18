data "aws_availability_zones" "available" {
  state = "available"
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = var.environment_name
  cidr = "10.0.0.0/16"

  azs              = data.aws_availability_zones.available.names
  private_subnets  = ["10.0.0.0/24", "10.0.1.0/24"]
  public_subnets = ["10.0.10.0/24"]

  enable_dns_hostnames            = true
  enable_nat_gateway              = true
  single_nat_gateway = true
}
