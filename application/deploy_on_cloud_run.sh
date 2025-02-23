#!/bin/bash
SERVICE_NAME=chat-backend-test
REGION=europe-west3
SERVICE_ACCOUNT=si-cdc-chatbot-backend@psi-n-cdc-dev-887f.iam.gserviceaccount.com
MEMORY=4Gi
PORT=8000
gcloud run deploy $SERVICE_NAME \
 --source .  \
 --service-account $SERVICE_ACCOUNT \
 --memory $MEMORY \
 --ingress all \
 --region $REGION \
 --port $PORT
