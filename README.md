## GenerativeAI Weltwissen: Backend

#### Push des Docker Images

Das Docker Image wid über gcloud builds "submit --project=PROJECT_ID --region=europe-west3 --tag=AR_PATH/IMAGE_NAME:latest" in die Artifact Registry gepusht.

#### Integration in Cloud Run

Die Umgebungsvariable "CHATBOT_LOGGING_BUCKET" muss gesetzt sein. Hier wird der Cloud Storage Bucket angegeben, in welchen die Chatbot-Konversationen geloggt werden.
Die Application läuft standardmäßig auf Port 8080.

#### Deployment der Anwendung

Die Anwendung wird über `terraform` ausgerollt, wie hier am Beispiel der Stage `dev`:

```bash
$ cd ./infrastructure
$ terraform init -backend-config=./envs/dev/backend.conf
$ terraform plan -var-file=./envs/dev/terraform.tfvars
```

Forcieren des Deloyments einer neuen Revision in Cloud Run:

```bash
$ terraform apply -var-file=./envs/dev/terraform.tfvars
```
