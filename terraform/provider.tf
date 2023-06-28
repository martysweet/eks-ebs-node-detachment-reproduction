terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
    kubernetes = {
      source = "hashicorp/kubernetes"
    }
  }
}

provider "aws" {
  region = "eu-west-1"

  default_tags {
    tags = {
      Terraform   = "True"
    }
  }
}

#data "aws_eks_cluster" "cluster" {
#  name = var.environment_name
#}
#
#data "aws_eks_cluster_auth" "cluster" {
#  name = var.environment_name
#}
#data "aws_caller_identity" "current" {}
#
#locals {
#  openid_provider_url = data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer
#  openid_domain       = split("/", local.openid_provider_url)[2]
#  openid_provider     = split("/", local.openid_provider_url)[4]
#  openid_provider_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${local.openid_domain}/id/${local.openid_provider}"
#}
#
#provider "kubernetes" {
#  host                   = data.aws_eks_cluster.cluster.endpoint
#  cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority.0.data)
#  token                  = data.aws_eks_cluster_auth.cluster.token
#}
#
#provider "helm" {
#  kubernetes {
#    host                   = data.aws_eks_cluster.cluster.endpoint
#    cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority.0.data)
#    token                  = data.aws_eks_cluster_auth.cluster.token
#  }
#}

