locals {
  service_account_project_roles = {
    (var.project_id) = [
      "roles/aiplatform.admin",
      "roles/logging.logWriter",
      "roles/artifactregistry.reader",
      "roles/dlp.user",
      "roles/storage.admin",
      "roles/discoveryengine.admin"
  ] }

  static_envs = {
    CHATBOT_LOGGING_BUCKET = {
      value = module.storage_bucket.bucket_name
    },
    CONNECTION_STRING = {
      secret_id      = module.secret_ssl["connection-string"].id
      secret_version = "latest"
    },
    DATASTORE_ID = {
      value = module.agent_builder.data_store_id
    }
  }

  container_envs        = merge(local.static_envs, var.container_envs)
  private_key_dir       = "/ssl-private-key"
  cert_dir              = "/ssl-certificate"
  private_key_file_name = "cert.key"
  cert_file_name        = "cert.pem"
  connection_string     = "postgresql://${var.database_user_name}:${module.cloud_sql.users[var.database_user_name].password}@${module.cloud_sql.ip_address}/${var.database_name}?sslcert=${local.cert_dir}/${local.cert_file_name}&sslkey=${local.private_key_dir}/${local.private_key_file_name}"

  alembic_job_name = join("-", compact([
    var.context.prefix,
    var.context.workload,
    var.context.stage,
    var.context.capability,
    "alembic-migration"
  ]))
}
