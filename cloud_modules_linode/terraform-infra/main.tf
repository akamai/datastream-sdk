variable "linode_api_token" {
  description = "Linode API Token"
  type        = string
}

variable "tenant_id" {
  description = "Tenant ID for bucket naming"
  type        = string
}

variable "input_storage_region" {
  description = "Region for Input Storage"
  type        = string
  default     = "us-east"
}

variable "output_storage_region" {
  description = "Region for Output Storage"
  type        = string
  default     = "us-east"
}

variable "config_storage_region" {
  description = "Region for Configuration Storage"
  type        = string
  default     = "us-east"
}

variable "monitor_storage_region" {
  description = "Region for Monitor Storage"
  type        = string
  default     = "us-east"
}

variable "lke_cluster_region" {
  description = "Region for LKE Cluster"
  type        = string
  default     = "us-east"
}

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
  region = var.input_storage_region
}

resource "linode_object_storage_key" "data_input_storage_key" {
  depends_on = [linode_object_storage_bucket.data_input_storage]
  label = "data-input-storage-key-${var.tenant_id}"
  bucket_access {
    region      = linode_object_storage_bucket.data_input_storage.region
    bucket_name = linode_object_storage_bucket.data_input_storage.label
    permissions = "read_write"
  }
}

resource "linode_object_storage_bucket" "data_output_storage" {
  label  = "data-output-storage-${var.tenant_id}"
  region = var.output_storage_region
}

resource "linode_object_storage_key" "data_output_storage_key" {
  depends_on = [linode_object_storage_bucket.data_output_storage]
  label = "data-output-storage-key-${var.tenant_id}"
  bucket_access {
    region      = linode_object_storage_bucket.data_output_storage.region
    bucket_name = linode_object_storage_bucket.data_output_storage.label
    permissions = "read_write"
  }
}

resource "linode_object_storage_bucket" "monitor_storage" {
  label  = "monitor-storage-${var.tenant_id}"
  region = var.monitor_storage_region
}

resource "linode_object_storage_key" "monitor_storage_key" {
  depends_on = [linode_object_storage_bucket.monitor_storage]
  label = "monitor-storage-key-${var.tenant_id}"
  bucket_access {
    region      = linode_object_storage_bucket.monitor_storage.region
    bucket_name = linode_object_storage_bucket.monitor_storage.label
    permissions = "read_write"
  }
}

resource "linode_object_storage_bucket" "configuration_storage" {
  label  = "configuration-storage-${var.tenant_id}"
  region = var.config_storage_region
}

resource "linode_object_storage_key" "configuration_storage_key" {
  depends_on = [linode_object_storage_bucket.configuration_storage]
  label = "configuration-storage-key-${var.tenant_id}"
  bucket_access {
    region      = linode_object_storage_bucket.configuration_storage.region
    bucket_name = linode_object_storage_bucket.configuration_storage.label
    permissions = "read_write"
  }
}

resource "linode_lke_cluster" "datastream_lke_cluster" {
  label       = "datastream-lke-cluster-${var.tenant_id}"
  region      = var.lke_cluster_region
  k8s_version = "1.33"

  pool {
    type  = "g6-standard-1"
    count = 3
  }
}

resource "local_file" "kubeconfig" {
  depends_on = [linode_lke_cluster.datastream_lke_cluster]
  filename = "${path.module}/kubeconfig-${var.tenant_id}.yaml"
  content = base64decode(linode_lke_cluster.datastream_lke_cluster.kubeconfig)
}

output "tenant_id" {
  value = var.tenant_id
}

output "data_input_storage_secret" {
  value = {
    storage_name = linode_object_storage_bucket.data_input_storage.label
    region       = linode_object_storage_bucket.data_input_storage.region
    access_key   = linode_object_storage_key.data_input_storage_key.access_key
    secret_key   = linode_object_storage_key.data_input_storage_key.secret_key
  }
  sensitive = true
}

output "data_output_storage_secret" {
  value = {
    storage_name = linode_object_storage_bucket.data_output_storage.label
    region       = linode_object_storage_bucket.data_output_storage.region
    access_key   = linode_object_storage_key.data_output_storage_key.access_key
    secret_key   = linode_object_storage_key.data_output_storage_key.secret_key
  }
  sensitive = true
}

output "monitor_storage_secret" {
  value = {
    storage_name = linode_object_storage_bucket.monitor_storage.label
    region       = linode_object_storage_bucket.monitor_storage.region
    access_key   = linode_object_storage_key.monitor_storage_key.access_key
    secret_key   = linode_object_storage_key.monitor_storage_key.secret_key
  }
  sensitive = true
}

output "configuration_storage_secret" {
  value = {
    storage_name = linode_object_storage_bucket.configuration_storage.label
    region       = linode_object_storage_bucket.configuration_storage.region
    access_key   = linode_object_storage_key.configuration_storage_key.access_key
    secret_key   = linode_object_storage_key.configuration_storage_key.secret_key
  }
  sensitive = true
}
