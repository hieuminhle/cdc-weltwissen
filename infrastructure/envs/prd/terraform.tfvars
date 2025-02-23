context = {
  prefix   = "si"
  workload = "chatbot"
  stage    = "prd"
  suffix   = "backend"
}

project_id       = "psi-p-chatbot-prd-8f0f"
vpc_network_name = "psi-p-chatbot-prd"
vpc_subnet_name  = "psi-p-chatbot-prd-europe-west3-535a"

region = "europe-west3"

encryption_key = "projects/psi-p-chatbot-prd-8f0f/locations/europe-west3/keyRings/si-chatbot-prod-keyring/cryptoKeys/si-chatbot-prod-key"
container_envs = {
  PROJECT_ID = {
    value = "psi-p-chatbot-prd-8f0f"
  }
}

frontend_service_account_name     = "oauth-proxy-sidecar-swof@psi-p-chatbot-prd-8f0f.iam.gserviceaccount.com"
plugin_proxy_service_account_name = "oauth-proxy-sidecar-ganl@psi-p-chatbot-prd-8f0f.iam.gserviceaccount.com"
