terraform {
  required_providers {
    linode = {
      source  = "linode/linode"
      version = ">=3.0.0"
    }
  }
}

provider "linode" {
  token = var.linode_api_token
}

resource "linode_object_storage_bucket" "data_input_storage" {
  label  = "data-input-storage-${var.tenant_id}"
  region = var.region
}

resource "linode_object_storage_bucket" "monitor_storage" {
  label  = "monitor-storage-${var.tenant_id}"
  region = var.region
}

resource "linode_object_storage_bucket" "configuration_storage" {
  label  = "configuration-storage-${var.tenant_id}"
  region = var.region
}

resource "linode_object_storage_key" "data_input_storage_key" {
  label = "data-input-storage-key-${var.tenant_id}"
  bucket_access {
    region      = linode_object_storage_bucket.data_input_storage.region
    bucket_name = linode_object_storage_bucket.data_input_storage.label
    permissions = "read_write"
  }
}

resource "linode_object_storage_key" "monitor_storage_key" {
  label = "monitor-storage-key-${var.tenant_id}"
  bucket_access {
    region      = linode_object_storage_bucket.monitor_storage.region
    bucket_name = linode_object_storage_bucket.monitor_storage.label
    permissions = "read_write"
  }
}

resource "linode_object_storage_key" "configuration_storage_key" {
  label = "configuration-storage-key-${var.tenant_id}"
  bucket_access {
    region      = linode_object_storage_bucket.configuration_storage.region
    bucket_name = linode_object_storage_bucket.configuration_storage.label
    permissions = "read_write"
  }
}

resource "linode_database_postgresql_v2" "postgresql" {
  label     = "result-db-${var.tenant_id}"
  engine_id = "postgresql/17"
  region    = var.region
  type      = "g6-nanode-1"
}

resource "linode_lke_cluster" "main" {
  label       = "datastream-lke-cluster-${var.tenant_id}"
  region      = var.region
  k8s_version = "1.33"

  pool {
    type  = "g6-standard-1"
    count = 3
  }
}

resource "local_file" "kubeconfig" {
  depends_on = [linode_lke_cluster.main]
  filename = "${path.module}/kubeconfig-${var.tenant_id}.yaml"
  content = base64decode(linode_lke_cluster.main.kubeconfig)
}

output "data_input_storage_access_key" {
  value = linode_object_storage_key.data_input_storage_key.access_key
  sensitive = true
}

output "data_input_storage_secret_key" {
  value = linode_object_storage_key.data_input_storage_key.secret_key
  sensitive = true
}

output "monitor_storage_access_key" {
  value = linode_object_storage_key.monitor_storage_key.access_key
  sensitive = true
}

output "monitor_storage_secret_key" {
  value = linode_object_storage_key.monitor_storage_key.secret_key
  sensitive = true
}

output "configuration_storage_access_key" {
  value = linode_object_storage_key.configuration_storage_key.access_key
  sensitive = true
}

output "configuration_storage_secret_key" {
  value = linode_object_storage_key.configuration_storage_key.secret_key
  sensitive = true
}

output "data_input_storage_label" {
  value = linode_object_storage_bucket.data_input_storage.label
}

output "monitor_storage_label" {
  value = linode_object_storage_bucket.monitor_storage.label
}

output "configuration_storage_label" {
  value = linode_object_storage_bucket.configuration_storage.label
}

output "tenant_id" {
  value = var.tenant_id
}

output "region" {
  value = var.region
}

variable "linode_api_token" {
  description = "Linode API Token"
  type        = string
}

variable "tenant_id" {
  description = "Tenant ID for bucket naming"
  type        = string
}

variable "region" {
  description = "Region for all resources"
  type        = string
  default     = "us-east"
}
