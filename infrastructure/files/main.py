import os
import json
import logging
import hashlib
import google.cloud.logging
from google.cloud import storage
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1alpha as discoveryengine

# Logging clients
logging_client = google.cloud.logging.Client()
logging_client.setup_logging()

# Environment variables
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
DATA_STORE_ID = os.getenv("DATA_STORE_ID")
GCS_BUCKET = os.getenv("GCS_BUCKET")
METADATA_BASE_DIR = "metadata"

def import_documents(project_id, location, data_store_id, event_bucket, metadata_filename):
    # Create a client
    client_options = (
        ClientOptions(
            api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )
    client = discoveryengine.DocumentServiceClient(
        client_options=client_options)

    # The full resource name of the search engine branch.
    # e.g. projects/{project}/locations/{location}/dataStores/{data_store_id}/branches/{branch}
    parent = client.branch_path(
        project=project_id,
        location=location,
        data_store=data_store_id,
        branch="default_branch",
    )

    document_metadata = [f'gs://{event_bucket}/{metadata_filename}']

    request_metadata = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(
            input_uris=document_metadata, data_schema="document"
        ),
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
    )

    operation_metadata = client.import_documents(request=request_metadata)

    response_metadata =  operation_metadata.result()

    metadata = discoveryengine.ImportDocumentsMetadata(operation_metadata.metadata)

    # Handle the response
    return operation_metadata.operation.name

def write_metadata_file(bucket: str, file_path: str):
    blob_gcs_uri = f"gs://{bucket}/{file_path}"
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET)
    doc_id = hashlib.md5(blob_gcs_uri.encode()).hexdigest()[:8]
    metadata_filename = f"{METADATA_BASE_DIR}/{doc_id}.jsonl"

    blob = bucket.blob(metadata_filename)
    sharepoint_url_prefix = "https://si365.sharepoint.com/:b:/r/sites/p0124/Freigegebene%20Dokumente/"
    sharepoint_uri = sharepoint_url_prefix + file_path.replace(" ", "%20")

    match blob_gcs_uri.split(".")[-1]:
        case "pdf":
            mime_type = "application/pdf"
        case "xlsx":
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        case "pptx":
            mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        case "docx":
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        case _:
            mime_type = "text/html"

    logging.info("Mime type: " + mime_type)

    # mime_type = "application/pdf" if blob_gcs_uri.split(".")[1] == "pdf" else "text/html"
    jsonl_new_data = f'{{"id":"{doc_id}", "structData":{{"sharepoint_uri":"{sharepoint_uri}"}},"content":{{"mimeType":"{mime_type}","uri":"{blob_gcs_uri}"}}}}'
    blob.upload_from_string(data=jsonl_new_data, content_type="text/plain")
    logging.info(f"File metadata written to json_file: {metadata_filename}")
    return metadata_filename

def event_handler(event, context):
    try:
        if event["name"].split("/")[0] == METADATA_BASE_DIR:
            return
        object_id = f'gs://{event["bucket"]}/{event["name"]}'
        logging.info('object_id: %s', object_id)
        logging.info(f"Reading metadata for object")
        metadata_filename = write_metadata_file(event["bucket"], event["name"])
        logging.info('Starting loading data %s into data store', event["name"])
        import_documents(PROJECT_ID, LOCATION, DATA_STORE_ID, event["bucket"], metadata_filename)
        logging.info('Completed loading data %s into data store', event["name"])

    except Exception as e:
        logging.error('Error: %s', e)


if __name__ == "__main__":
    test_event = {'bucket': GCS_BUCKET, 'name': 'test.pdf'}
    event_handler(test_event, context)
