variable "context" {
  description = "The context in which the cloud run service will be deployed. This is used to locate the resources and to generate the service name."
  type = object({
    prefix     = string
    workload   = string
    stage      = string
    capability = optional(string, "web")
    suffix     = optional(string, "backend")
  })
}

variable "project_id" {
  description = "ID of the project where the resources will be deployed."
  type        = string
}

variable "region" {
  description = "Project region where the resources will be deployed."
  type        = string
}

variable "container_envs" {
  description = "Environment variables passed to the Cloud Run container. "
  type = map(object({
    value          = optional(string, "")
    secret_id      = optional(string, null)
    secret_version = optional(string, null)
  }))
}

variable "encryption_key" {
  description = "ID of the encryption to be used for this deployment."
  type        = string
}

variable "labels" {
  description = "Resource labels."
  type        = map(string)
  default     = {}
}

variable "frontend_service_account_name" {
  description = "Name of the SI Chatbot frontend service account."
  type        = string
}

variable "plugin_proxy_service_account_name" {
  description = "Name of the SI Chatbot plugin proxy service account."
  type        = string
}

variable "vpc_network_name" {
  description = "Name of the VPC network where the SQL instance will be deployed and the Cloud Run egress will be routed."
  type        = string
}

variable "vpc_subnet_name" {
  description = "Name of the VPC subnet where the egress traffic of Cloud Run should be routed."
  type        = string
}

variable "instance_name" {
  description = "Name of the SQL instance."
  type        = string
  default     = "cosi"
}

variable "database_user_name" {
  description = "Name of the database user."
  type        = string
  default     = "cosi-admin"
}

variable "database_name" {
  description = "Name of the database."
  type        = string
  default     = "cosi-logs"
}
