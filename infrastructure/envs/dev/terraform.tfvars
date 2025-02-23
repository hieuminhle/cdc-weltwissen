context = {
  prefix   = "si"
  workload = "weltwissen"
  stage    = "dev"
  suffix   = "backend"
}

project_id       = "psi-n-chatbot-dev-b15c"
vpc_network_name = "psi-n-chatbot-dev"
vpc_subnet_name  = "psi-n-chatbot-dev-europe-west3-7191"

region = "europe-west3"

encryption_key = "projects/psi-n-chatbot-dev-b15c/locations/europe-west3/keyRings/si-chatbot-dev-keyring/cryptoKeys/si-chatbot-dev-key"

container_envs = {
  PROJECT_ID = {
    value = "psi-n-chatbot-dev-b15c"
  }
  DATASTORE_LOCATION = {
    value = "eu"
  }
  DATASTORE_ID = {
    value = "si-cdc-weltwissen-dev-bafin-docs_1728653094458"
  }
}

frontend_service_account_name     = "oauth-proxy-sidecar-3xp0@psi-n-chatbot-dev-b15c.iam.gserviceaccount.com"
plugin_proxy_service_account_name = "oauth-proxy-sidecar-rrdw@psi-n-chatbot-dev-b15c.iam.gserviceaccount.com"
