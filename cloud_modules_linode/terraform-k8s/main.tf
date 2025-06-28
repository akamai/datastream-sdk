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

resource "kubernetes_namespace" "tenant" {
  metadata {
    name = data.terraform_remote_state.infra.outputs.tenant_id
  }
}

resource "kubernetes_secret" "data_input_storage" {
  metadata {
    name      = "data-input-storage-secret"
    namespace = data.terraform_remote_state.infra.outputs.tenant_id
  }
  data = {
    storage_name = data.terraform_remote_state.infra.outputs.data_input_storage_secret.storage_name
    region       = data.terraform_remote_state.infra.outputs.data_input_storage_secret.region
    access_key   = data.terraform_remote_state.infra.outputs.data_input_storage_secret.access_key
    secret_key   = data.terraform_remote_state.infra.outputs.data_input_storage_secret.secret_key
  }
}

resource "kubernetes_secret" "data_output_storage" {
  metadata {
    name      = "data-output-storage-secret"
    namespace = data.terraform_remote_state.infra.outputs.tenant_id
  }
  data = {
    storage_name = data.terraform_remote_state.infra.outputs.data_output_storage_secret.storage_name
    region       = data.terraform_remote_state.infra.outputs.data_output_storage_secret.region
    access_key   = data.terraform_remote_state.infra.outputs.data_output_storage_secret.access_key
    secret_key   = data.terraform_remote_state.infra.outputs.data_output_storage_secret.secret_key
  }
}

resource "kubernetes_secret" "monitor_storage" {
  metadata {
    name      = "monitor-storage-secret"
    namespace = data.terraform_remote_state.infra.outputs.tenant_id
  }
  data = {
    storage_name = data.terraform_remote_state.infra.outputs.monitor_storage_secret.storage_name
    region       = data.terraform_remote_state.infra.outputs.monitor_storage_secret.region
    access_key   = data.terraform_remote_state.infra.outputs.monitor_storage_secret.access_key
    secret_key   = data.terraform_remote_state.infra.outputs.monitor_storage_secret.secret_key
  }
}

resource "kubernetes_secret" "configuration_storage" {
  metadata {
    name      = "configuration-storage-secret"
    namespace = data.terraform_remote_state.infra.outputs.tenant_id
  }
  data = {
    storage_name = data.terraform_remote_state.infra.outputs.configuration_storage_secret.storage_name
    region       = data.terraform_remote_state.infra.outputs.configuration_storage_secret.region
    access_key   = data.terraform_remote_state.infra.outputs.configuration_storage_secret.access_key
    secret_key   = data.terraform_remote_state.infra.outputs.configuration_storage_secret.secret_key
  }
}

resource "helm_release" "datastream_sdk" {
  depends_on = [
    kubernetes_namespace.tenant, kubernetes_secret.data_input_storage, kubernetes_secret.data_output_storage,
    kubernetes_secret.monitor_storage, kubernetes_secret.configuration_storage
  ]
  name      = "datastream-sdk"
  chart     = "https://mzupnik-a.github.io/datastream-sdk/datastream-sdk-0.1.0.tgz"
  repository_username = var.github_username
  repository_password = var.github_token
  namespace = data.terraform_remote_state.infra.outputs.tenant_id
}
