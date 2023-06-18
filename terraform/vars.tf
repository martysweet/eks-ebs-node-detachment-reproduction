variable "environment_name" {
  default = "ebs-test-cluster"
}

variable "kubernetes_version" {
  type        = string
  description = "Version of Kubernetes to deploy"
  default     = "1.27"
}
