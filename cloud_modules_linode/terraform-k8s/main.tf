variable "github_username" {
  description = "GitHub username for accessing the GitHub Container or Pages registry"
  type        = string
}

variable "github_token" {
  description = "GitHub token with read:packages or repo access"
  type        = string
  sensitive   = true
}

terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.37.1"
    }
    helm = {
      source  = "hashicorp/helm"
      version = ">= 3.0.2"
    }
  }
}

data "terraform_remote_state" "infra" {
  backend = "local"
  config = {
    path = "../terraform-infra/terraform.tfstate"
  }
}

provider "kubernetes" {
  config_path = "${path.module}/../terraform-infra/kubeconfig-${data.terraform_remote_state.infra.outputs.tenant_id}.yaml"
}

provider "helm" {
  kubernetes = {
    config_path = "${path.module}/../terraform-infra/kubeconfig-${data.terraform_remote_state.infra.outputs.tenant_id}.yaml"
  }
}

resource "helm_release" "datastream_sdk" {
  name      = "datastream-sdk"
  chart     = "https://mzupnik-a.github.io/datastream-sdk/datastream-sdk-0.1.0.tgz"
  repository_username = var.github_username   // <-- Pass as a variable
  repository_password = var.github_token      // <-- Pass as a variable
  namespace = data.terraform_remote_state.infra.outputs.tenant_id
}