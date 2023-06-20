module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = var.environment_name
  cluster_version = var.kubernetes_version

  cluster_endpoint_public_access = true

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  create_cloudwatch_log_group = true
  cluster_enabled_log_types   = ["audit", "api", "authenticator", "controllerManager", "scheduler"]

  eks_managed_node_group_defaults = {
    iam_role_additional_policies = {
      AmazonSSMManagedInstanceCore = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
    }
  }

  eks_managed_node_groups = {
    core = {
      # Run any supporting resources such as controllers
      min_size       = 1
      max_size       = 1
      desired_size   = 1
      instance_types = ["t3a.large"]

      capacity_type = "SPOT"
    }
    testcase = {
      # Dedicated to running EBS Helm for reproduction
      min_size       = 2
      max_size       = 2
      desired_size   = 2
      instance_types = ["t3a.large"]

      subnet_ids         = [module.vpc.private_subnets[0]] # Force single AZ for EBS ease of node placement

      labels = {
        node_role = "test"
      }

      taints = [
        {
          key    = "node_role"
          value  = "test"
          effect = "NO_SCHEDULE"
        }
      ]
    }
  }

  # aws-auth configmap
  create_aws_auth_configmap = true
  manage_aws_auth_configmap = true
}

module "eks_blueprints_addons" {
  source = "aws-ia/eks-blueprints-addons/aws"

  cluster_name      = module.eks.cluster_name
  cluster_endpoint  = module.eks.cluster_endpoint
  cluster_version   = module.eks.cluster_version
  oidc_provider_arn = module.eks.oidc_provider_arn

  eks_addons = {
    aws-ebs-csi-driver = {
      most_recent              = true
      service_account_role_arn = module.ebs_csi_driver_irsa.iam_role_arn
    }
    coredns = {
      most_recent = true
    }
    vpc-cni = {
      most_recent              = true
      service_account_role_arn = module.vpc_cni_irsa.iam_role_arn
    }
    kube-proxy = {
      most_recent = true
    }
  }

  enable_metrics_server               = false
  enable_aws_load_balancer_controller = false
  enable_aws_cloudwatch_metrics       = false
  enable_aws_for_fluentbit            = false
  enable_karpenter                    = false
  enable_kube_prometheus_stack        = false
  enable_argocd                       = false
  enable_external_secrets             = false
  enable_ingress_nginx                = false
  enable_external_dns                 = false
}
