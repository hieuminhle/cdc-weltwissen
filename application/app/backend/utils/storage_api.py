from google.cloud import storage
from . import constants
import os
from typing import List, Optional
import json
from datetime import datetime

storage_client = storage.Client(project=os.environ["PROJECT_ID"])

def write_bucket_object(
    blob_name: str,
    object_content: str,
    bucket_name: str = os.environ["CHATBOT_LOGGING_BUCKET"],
) -> None:
    storage_client = storage.Client(project=os.environ["PROJECT_ID"])
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    with blob.open("w") as f:
        f.write(object_content)


def log_history(
    session_id:str,
    oid_hashed:str,
    chat_type:str,
    history:list, #List[Conversation],
    bucket_name:str,
    context:Optional[str]=None,
):
   # convert Conversation-Objects to JSON-Strings
    history_json = [ json.loads(c.json()) for c in history ]

    if context == None:
        context = constants.DEFAULT_CONTEXT

    # oid_hashed not saved yet due to internal data protection policy
    text_messages_json: str = json.dumps(
        {
            "session_id": session_id,
            "chat_type":chat_type,
            "chat_history": history_json,
            "context":context
        },
        ensure_ascii=False
    )

    CURRENT_DATE = datetime.today().strftime("%Y-%m-%d")

    write_bucket_object(
        f"{CURRENT_DATE}/{session_id}.txt",
            text_messages_json,
            bucket_name
    )
