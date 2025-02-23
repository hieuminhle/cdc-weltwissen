module "storage_bucket" {
  source         = "git::https://git.system.local/scm/cdc/si-cdc-tf-modules//modules/cloud-storage?ref=cba2b65ce7c6d424671116db09a2aa0678865ede"
  project_id     = var.project_id
  context        = var.context
  capability     = "logging"
  suffix         = var.context.suffix
  encryption_key = var.encryption_key
  lifecycle_rules = {
    "max_90_days" = {
      action = {
        type = "Delete"
      }
      condition = {
        age = 90
      }
    }
  }
}

module "service_account" {
  source            = "git::https://git.system.local/scm/cdc/si-cdc-tf-modules//modules/iam-service-account?ref=cba2b65ce7c6d424671116db09a2aa0678865ede"
  project_id        = var.project_id
  name              = "si-chatbot-backend"
  suffix            = random_string.this[0].result
  description       = "Service Account for a Cloud Run service that hosts the backend of the SI Chatbot."
  iam_members       = {}
  iam_project_roles = local.service_account_project_roles
}

resource "random_string" "this" {
  count   = 2
  length  = 4
  special = false
  upper   = false
}

module "artifact_registry_repository" {
  source         = "git::https://git.system.local/scm/cdc/si-cdc-tf-modules//modules/artifact-registry?ref=cba2b65ce7c6d424671116db09a2aa0678865ede"
  project_id     = var.project_id
  context        = var.context
  capability     = var.context.capability
  suffix         = var.context.suffix
  labels         = var.labels
  encryption_key = var.encryption_key
}

module "cloud_run" {
  source          = "git::https://git.system.local/scm/cdc/si-cdc-tf-modules//modules/cloud-run?ref=v0.3.3"
  project_id      = var.project_id
  region          = var.region
  context         = var.context
  suffix          = var.context.suffix
  labels          = var.labels
  service_account = module.service_account.email
  iam = {
    "roles/run.invoker" = ["serviceAccount:${var.frontend_service_account_name}", "serviceAccount:${var.plugin_proxy_service_account_name}"]
  }
  description    = "Backend service for the Chat@SI Chatbot."
  encryption_key = var.encryption_key
  ingress        = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  containers = {
    "main" = {
      image = module.docker_image.image_sha
      ports = [{
        container_port = 8080
      }]
      env = local.container_envs
      volume_mounts = {
        ssl-cert    = local.cert_dir
        private-key = local.private_key_dir
      }
      liveness_probe = {
        action = {
          http_get = {
            port = 8080
            path = "/health"
          }
        }
      }
      resources = {
        limits = {
          cpu    = "1"
          memory = "1024Mi"
        }
      }
    }
  }
  autoscaling = {
    min = 1
    max = 10
  }
  vpc_access = {
    egress = "ALL_TRAFFIC"
    direct = {
      network    = var.vpc_network_name
      subnetwork = var.vpc_subnet_name
    }
  }
  volumes = {
    ssl-cert = {
      secret_name  = module.secret_ssl["ssl-cert"].id
      default_mode = 384 # 0600
      items = {
        latest = {
          path = local.cert_file_name
        }
      }
    }
    private-key = {
      secret_name  = module.secret_ssl["private-key"].id
      default_mode = 384 # 0600
      items = {
        latest = {
          path = local.private_key_file_name
        }
      }
    }
  }
  container_concurrency = "80"
  depends_on            = [module.docker_image, google_cloud_run_v2_job.default]
}

module "docker_image" {
  source     = "git::https://git.system.local/scm/cdc/si-cdc-tf-modules//modules/docker-image?ref=bdb220aec03c0c19e934c7e1a485ed52ba52617c"
  project_id = var.project_id
  context    = var.context
  capability = var.context.capability
  suffix     = var.context.suffix
  repository = {
    name = module.artifact_registry_repository.name
  }
  source_path = "../application"
  additional_triggers = {
    artifact_registry = module.artifact_registry_repository.name
  }
}

module "cloud_sql" {
  source     = "git::https://git.system.local/scm/cdc/si-cdc-tf-modules//modules/cloud-sql?ref=feature/cloud-sql-module"
  project_id = var.project_id
  context = {
    prefix     = var.context.prefix
    workload   = var.context.workload
    stage      = var.context.stage
    capability = var.context.capability
    suffix     = ""
  }
  instance_name = var.instance_name
  ipv4_enabled  = false
  private_ip_config = {
    network_ip_range = null
    network_name     = var.vpc_network_name
  }
  database_name              = var.database_name
  encryption_key             = var.encryption_key
  deletion_protection        = false
  password_special_overrides = "!#$&*()-_=+[]{}<>?"
  users = [
    {
      name = var.database_user_name
    }
  ]
}


resource "google_cloud_run_v2_job" "default" {
  name     = local.alembic_job_name
  location = "europe-west3"
  template {
    task_count = 1
    template {
      containers {
        image = module.docker_image_alembic.image_sha
        volume_mounts {
          name       = "certificate"
          mount_path = local.cert_dir
        }
        volume_mounts {
          name       = "private-key"
          mount_path = local.private_key_dir
        }
        env {
          name = "CONNECTION_STRING"
          value_source {
            secret_key_ref {
              secret  = module.secret_ssl["connection-string"].id
              version = "latest"
            }
          }
        }
      }
      service_account = module.service_account_alembic.email
      encryption_key  = var.encryption_key
      vpc_access {
        egress = "ALL_TRAFFIC"
        network_interfaces {
          network    = var.vpc_network_name
          subnetwork = var.vpc_subnet_name
        }
      }
      volumes {
        name = "certificate"
        secret {
          secret       = module.secret_ssl["ssl-cert"].id
          default_mode = 384 # 0600
          items {
            version = "latest"
            path    = local.cert_file_name
          }
        }
      }
      volumes {
        name = "private-key"
        secret {
          secret       = module.secret_ssl["private-key"].id
          default_mode = 384 # 0600
          items {
            version = "latest"
            path    = local.private_key_file_name
          }
        }
      }
    }
  }
  depends_on = [module.secret_ssl, google_kms_crypto_key_iam_member.crypto_key]
}

module "docker_image_alembic" {
  source     = "git::https://git.system.local/scm/cdc/si-cdc-tf-modules//modules/docker-image?ref=bdb220aec03c0c19e934c7e1a485ed52ba52617c"
  project_id = var.project_id
  context    = var.context
  capability = var.context.capability
  suffix     = join("-", compact([var.context.suffix, "alembic"]))
  repository = {
    name = module.artifact_registry_repository.name
  }
  source_path = "../application/app/alembic"
  additional_triggers = {
    artifact_registry = module.artifact_registry_repository.name
  }
}

module "secret_ssl" {
  for_each = {
    "ssl-cert"          = module.cloud_sql.certificate
    "private-key"       = module.cloud_sql.private_key
    "connection-string" = local.connection_string
  }
  source         = "git::https://git.system.local/scm/cdc/si-cdc-tf-modules//modules/secret-manager?ref=v0.2.2"
  context        = var.context
  capability     = var.context.capability
  resource       = var.instance_name
  suffix         = each.key
  project_id     = var.project_id
  encryption_key = var.encryption_key
  data           = each.value
  secret_accessors = {
    cloud_run_backend = "serviceAccount:${module.service_account.email}"
    cloud_run_alembic = "serviceAccount:${module.service_account_alembic.email}"
  }
}

module "service_account_alembic" {
  source            = "git::https://git.system.local/scm/cdc/si-cdc-tf-modules//modules/iam-service-account?ref=cba2b65ce7c6d424671116db09a2aa0678865ede"
  project_id        = var.project_id
  name              = "si-chatbot-alembic"
  suffix            = random_string.this[1].result
  description       = "Service Account for a Cloud Run Job that runs the alembic migrations."
  iam_members       = {}
  iam_project_roles = local.service_account_project_roles
}

resource "google_kms_crypto_key_iam_member" "crypto_key" {
  for_each = {
    "alembic_sa"              = "serviceAccount:${module.service_account_alembic.email}"
    "cloud_run_service_agent" = "serviceAccount:service-${data.google_project.this.number}@serverless-robot-prod.iam.gserviceaccount.com"
  }
  crypto_key_id = var.encryption_key
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = each.value
}


resource "null_resource" "job_execution" {
  provisioner "local-exec" {
    command = "gcloud run jobs execute ${google_cloud_run_v2_job.default.name} --wait --region=${var.region} --project=${var.project_id}"
  }
  triggers = {
    alembic_migrations = module.docker_image_alembic.image_sha
  }
  depends_on = [google_cloud_run_v2_job.default]
}


module "agent_builder" {
  source                  = "git::https://git.system.local/scm/cdc/si-cdc-tf-modules//modules/agent-builder?ref=54f6a86c00d34bce38acf73c667eb5b2abd69a2e"
  project_id              = var.project_id
  context                 = var.context
  capability              = var.context.capability
  suffix                  = "bafin-docs"
  data_store_display_name = "BAFIN Docs Data Store"
  content_config          = "CONTENT_REQUIRED"
  collection_id           = "default_collection"
  engine_display_name     = "bafin-docs-search"
  encryption_key          = var.encryption_key
  parser_type             = "OCR_PARSER"
  bucket_name_suffix      = ["data-store"]
}

module "cloud_function" {
  count              = var.context.stage == "dev" ? 1 : 0
  source             = "git::https://git.system.local/scm/cdc/si-cdc-tf-modules//modules/cloud-functions-v2?ref=v0.3.11"
  project_id         = var.project_id
  context            = var.context
  capability         = var.context.capability
  resource           = "cf"
  suffix             = "ds"
  source_dir         = "${path.module}/files"
  entry_point        = "event_handler"
  runtime            = "python311"
  encryption_key     = var.encryption_key
  memory_in_mb       = 4196
  timeout_seconds    = 540
  max_instance_count = 100
  trigger_config = {
    event_type   = "google.cloud.storage.object.v1.finalized"
    retry_policy = "RETRY_POLICY_RETRY"
    event_filters = [{
      attribute = "bucket"
      value     = module.agent_builder.bucket_name
    }]
  }
  env_variables = {
    "PROJECT_ID"    = var.project_id
    "LOCATION"      = "eu"
    "DATA_STORE_ID" = module.agent_builder.data_store_id
    "GCS_BUCKET"    = module.agent_builder.bucket_name
  }
  labels               = var.labels
  storage_bucket_name  = module.gcs_bucket[0].bucket_name
  artifact_registry_id = module.artifact_registry_repository.id
  depends_on           = [module.gcs_bucket]
}

module "gcs_bucket" {
  count          = var.context.stage == "dev" ? 1 : 0
  source         = "git::https://git.system.local/scm/cdc/si-cdc-tf-modules//modules/cloud-storage?ref=v0.3.11"
  suffix         = "cf-source"
  project_id     = var.project_id
  context        = var.context
  capability     = var.context.capability
  encryption_key = var.encryption_key
  versioning     = true
  force_destroy  = true
  labels         = var.labels
}

resource "google_project_iam_member" "this" {
  count   = var.context.stage == "dev" ? 1 : 0
  project = var.project_id
  role    = "roles/discoveryengine.admin"
  member  = module.cloud_function[0].service_account.member
}

resource "google_storage_bucket_iam_member" "member" {
  count  = var.context.stage == "dev" ? 1 : 0
  bucket = module.agent_builder.bucket_name
  role   = "roles/storage.objectUser"
  member = module.cloud_function[0].service_account.member
}
