terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.37.1"
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

resource "kubernetes_namespace" "tenant" {
  metadata {
    name = data.terraform_remote_state.infra.outputs.tenant_id
  }
}

resource "kubernetes_secret" "data_input_storage" {
  metadata {
    name      = "data-input-storage-secret"
    namespace = kubernetes_namespace.tenant.metadata.0.name
  }
  data = {
    access_key = data.terraform_remote_state.infra.outputs.data_input_storage_access_key
    secret_key = data.terraform_remote_state.infra.outputs.data_input_storage_secret_key
  }
}

resource "kubernetes_secret" "monitor_storage" {
  metadata {
    name      = "monitor-storage-secret"
    namespace = kubernetes_namespace.tenant.metadata.0.name
  }
  data = {
    access_key = data.terraform_remote_state.infra.outputs.monitor_storage_access_key
    secret_key = data.terraform_remote_state.infra.outputs.monitor_storage_secret_key
  }
}

resource "kubernetes_secret" "configuration_storage" {
  metadata {
    name      = "configuration-storage-secret"
    namespace = kubernetes_namespace.tenant.metadata.0.name
  }
  data = {
    access_key = data.terraform_remote_state.infra.outputs.configuration_storage_access_key
    secret_key = data.terraform_remote_state.infra.outputs.configuration_storage_secret_key
  }
}

resource "kubernetes_config_map" "storage_buckets_config" {
  metadata {
    name      = "storage-buckets-config"
    namespace = kubernetes_namespace.tenant.metadata.0.name
  }
  data = {
    data_input_storage    = data.terraform_remote_state.infra.outputs.data_input_storage_label
    monitor_storage       = data.terraform_remote_state.infra.outputs.monitor_storage_label
    configuration_storage = data.terraform_remote_state.infra.outputs.configuration_storage_label
    region                = data.terraform_remote_state.infra.outputs.region
  }
}
