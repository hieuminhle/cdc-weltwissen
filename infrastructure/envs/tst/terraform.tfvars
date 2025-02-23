context = {
  prefix   = "si"
  workload = "chatbot"
  stage    = "tst"
  suffix   = "backend"
}

project_id       = "psi-n-chatbot-tst-046f"
vpc_network_name = "psi-n-chatbot-tst"
vpc_subnet_name  = "psi-n-chatbot-tst-europe-west3-d231"

region = "europe-west3"

encryption_key = "projects/psi-n-chatbot-tst-046f/locations/europe-west3/keyRings/si-weltwissen-dev-keyring/cryptoKeys/si-weltwissen-dev-key"

container_envs = {
  PROJECT_ID = {
    value = "psi-n-chatbot-tst-046f"
  }
  DATASTORE_LOCATION = {
    value = "eu"
  }
  DATASTORE_ID = {
    value = "si-chatbot-tst-data-store-bafin_1729609555250"
  }
}

frontend_service_account_name     = "oauth-proxy-sidecar-jqpf@psi-n-chatbot-tst-046f.iam.gserviceaccount.com"
plugin_proxy_service_account_name = "oauth-proxy-sidecar-gyko@psi-n-chatbot-tst-046f.iam.gserviceaccount.com"
