from __future__ import annotations
import random
import string
import base64
import io
from datetime import datetime
import os
import json
from typing import List, Any, Tuple
import requests
from functools import wraps

from google.cloud import storage
import google.oauth2.id_token
from google.auth import default
import vertexai
from vertexai.language_models import ChatModel, ChatSession, InputOutputTextPair, CodeChatModel, ChatMessage, TextGenerationResponse
from vertexai.generative_models import (GenerativeModel,
                                        GenerationResponse,
                                        Tool,
                                        Part,
                                        Content,
                                        HarmBlockThreshold,
                                        HarmCategory)
from vertexai.preview.vision_models import ImageGenerationModel
from vertexai.preview.generative_models import grounding as preview_grounding

from . import constants, storage_api
from backend.schemas.schemas import Conversation, BackendError



SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}


def randomword(length: int) -> str:
    """Generate a random id for a chat session."""
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


# Wrapper for time measurement
def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs) -> Tuple[Any, float]:
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        duration = end_time - start_time
        return result, int(duration.total_seconds())
    return wrapper

# Helper function to get the number of tokens of prompt and llm response for usage logging


def _get_num_token_gemini(gemini_response: GenerationResponse) -> (int, int):
    metadata = gemini_response.to_dict()["usage_metadata"]
    return int(metadata['prompt_token_count']), int(metadata['candidates_token_count'])


def _get_num_token_palm(palm_response: TextGenerationResponse) -> (int, int):
    metadata = palm_response._prediction_response.metadata
    return int(metadata['tokenMetadata']['inputTokenCount']['totalTokens']), int(metadata['tokenMetadata']['outputTokenCount']['totalTokens'])


def _get_content_history_from_conversation_list(conv_list: List[Conversation]):
    contents = []
    for conv in conv_list:
        contents.append(Content(role="user", parts=[
                        Part.from_text(conv.question)]))
        contents.append(Content(role="model", parts=[
                        Part.from_text(conv.answer)]))
    return contents


@measure_time
def ask_gemini_docchat_question(
        doc_context: str,
        prompt: str,
        project_id: str,
        history: List[Conversation],
        model_name: str,
        temperature: float = constants.GEMINI_TEXT_CHAT_DEFAULT_TEMPERATURE,
        max_output_tokens: int = constants.GEMINI_MAX_OUTPUT_TOKENS,
        system_instruction: list = constants.SYSTEM_INSTRUCTION_GEMINI_DOC_CHAT,
        location: str = "europe-west3") -> (str, int, int):
    config = {
        "max_output_tokens": max_output_tokens,
        "temperature": temperature,
        "top_p": 1
    }

    contents_history = [
        Content(role="user", parts=[Part.from_text("<KONTEXT> " + doc_context + " </KONTEXT>")]),
        Content(role="model", parts=[Part.from_text(constants.DOC_CHAT_PLACEHOLDER_MESSAGE)])
    ]

    contents_history.extend(_get_content_history_from_conversation_list(history))

    contents_history.append(
        Content(role="user", parts=[Part.from_text(prompt)])
    )

    vertexai.init(project=project_id, location=location)
    model = GenerativeModel(
        model_name,
        system_instruction=system_instruction
    )

    response = model.generate_content(
        contents=contents_history,
        generation_config=config,
        safety_settings=SAFETY_SETTINGS
    )

    num_prompt_token, num_response_token = _get_num_token_gemini(response)

    answer_str = response.candidates[0].content.parts[0].text
    return answer_str, num_prompt_token, num_response_token


@measure_time
def ask_gemini_textchat_question(
    prompt: str,
    project_id: str,
    history: List[Conversation],
    model_name: str = constants.GEMINI_TEXT_CHAT_DEFAULT_MODEL_NAME,
    temperature: float = constants.GEMINI_TEXT_CHAT_DEFAULT_TEMPERATURE,
    max_output_tokens: int = constants.GEMINI_MAX_OUTPUT_TOKENS,
    location: str = "europe-west3",
    system_instruction: list = constants.SYSTEM_INSTRUCTION_GEMINI_TEXT_CHAT,
) -> (str, int, int):
    config = {
        "max_output_tokens": max_output_tokens,
        "temperature": temperature,
        "top_p": 1
    }
    contents_history = _get_content_history_from_conversation_list(history)
    contents_history.append(
        Content(role="user", parts=[Part.from_text(prompt)])
    )
    vertexai.init(project=project_id, location=location)
    model = GenerativeModel(
        model_name,
        system_instruction=system_instruction
    )

    response = model.generate_content(
        contents=contents_history,
        generation_config=config,
        safety_settings=SAFETY_SETTINGS,
    )

    num_prompt_token, num_response_token = _get_num_token_gemini(response)

    answer_str = response.candidates[0].content.parts[0].text
    return answer_str, num_prompt_token, num_response_token


def build_codechat_message_history(history: list):
    message_history = []
    for conversation in history:
        message_history.append(
            ChatMessage(content=conversation.question, author="user"),
        )
        message_history.append(
            ChatMessage(content=conversation.answer, author="system"),
        )
    return message_history


@measure_time
def ask_codechat_question(
        prompt: str,
        project_id: str,
        history: List[Conversation],
        model_name: str = constants.CODE_CHAT_DEFAULT_MODEL_NAME,
        temperature: float = constants.TEXT_CHAT_DEFAULT_TEMPERATURE,
        max_output_tokens: int = constants.CODE_CHAT_MAX_OUTPUT_TOKENS,
        context: str = constants.DEFAULT_CONTEXT,
        location: str = "europe-west3") -> (str, int, int):

    vertexai.init(project=project_id, location=location)

    message_history = build_codechat_message_history(history)

    code_chat_model = CodeChatModel.from_pretrained(model_name)
    formatted_history = "".join([f"Frage: {conversation.question}\nAntwort: {conversation.answer}\n" for conversation in history])
    full_context = f"{context}\n{formatted_history}"

    # Add context/history
    code_chat_session = code_chat_model.start_chat(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        message_history=message_history,
    )
    response = code_chat_session.send_message(prompt)
    num_prompt_token, num_response_token = _get_num_token_palm(response)
    answer = str(response.text)

    return answer, num_prompt_token, num_response_token


@measure_time
def generate_image(
    prompt: str,
    project_id: str,
    history: List[Conversation],
    session_id: str,
    model_name: str = constants.IMAGEN_DEFAULT_MODEL_NAME,
    image_num=constants.IMAGEN_NUM_IMAGES,
    context: str = constants.DEFAULT_CONTEXT,
    location: str = "EU"
) -> (List[str], str, List[BackendError]):

    vertexai.init(project=project_id, location=location)

    translation_result, _ = ask_gemini_textchat_question(
        prompt,
        project_id,
        [],
        system_instruction=constants.SYSTEM_INSTRUCTION_TRANSLATION_IMAGEN
    )

    en_prompt, _, _ = translation_result

    CURRENT_DATE = datetime.today().strftime("%Y-%m-%d")
    storage_uri = f"gs://{os.environ['CHATBOT_LOGGING_BUCKET']}/imagen/{CURRENT_DATE}"

    model = ImageGenerationModel.from_pretrained(model_name)

    urls = []
    errors = []

    try:
        response = model.generate_images(
            prompt=en_prompt,
            number_of_images=image_num,
            output_gcs_uri=storage_uri,
            # ["block_most", "block_some", "block_few", "block_fewest"]
            safety_filter_level="block_few",
            # ["dont_allow", "allow_adult", "allow_all"]
            person_generation="dont_allow"
        )
        urls = [im._gcs_uri for im in response.images]

    except Exception as e:
        errors.append(BackendError(
            code="500",
            msg=f"{type(e)}:{str(e)}",
            status="EMPTY_RESPONSE"
        ))
        print(e, type(e))

    return urls, en_prompt, errors


# @measure_time
def ask_gemini_with_bafin_docs(
    prompt: str,
    project_id: str,
    history: List[Conversation],
    datastore_id: str,
    model_name: str = constants.GEMINI_TEXT_CHAT_DEFAULT_MODEL_NAME,
    temperature: float = constants.GEMINI_TEXT_CHAT_DEFAULT_TEMPERATURE,
    max_output_tokens: int = constants.GEMINI_MAX_OUTPUT_TOKENS,
    location: str = "europe-west3",
    system_instruction: list = constants.SYSTEM_INSTRUCTION_GEMINI_TEXT_CHAT,
) -> (str, int, int):
    config = {
        "max_output_tokens": max_output_tokens,
        "temperature": temperature,
        "top_p": 1
    }
    contents_history = _get_content_history_from_conversation_list(history)
    contents_history.append(
        Content(role="user", parts=[Part.from_text(prompt)])
    )
    vertexai.init(project=project_id, location=location)
    model = GenerativeModel(
        model_name,
        system_instruction=system_instruction
    )

    bafin_datastore_tool = Tool.from_retrieval(
        retrieval=preview_grounding.Retrieval(
            preview_grounding.VertexAISearch(
                datastore=datastore_id,
                project=project_id,
                location="eu"
            )
        )
    )

    response = model.generate_content(
        contents=contents_history,
        tools=[bafin_datastore_tool],
        generation_config=config,
        safety_settings=SAFETY_SETTINGS,
    )

    num_prompt_token, num_response_token = _get_num_token_gemini(response)

    answer_str = grounding_response_with_citations(response=response)
    return answer_str, num_prompt_token, num_response_token



def get_auth_token(req_uri: str):
    auth_req = google.auth.transport.requests.Request()
    credentials, _ = google.auth.default()
    credentials.refresh(auth_req)
    auth_token = credentials.token
    # print(f"Auth Token: \n\n\n{auth_token}")
    return auth_token

#### Helper Function

# source: https://github.com/GoogleCloudPlatform/generative-ai/blob/main/gemini/grounding/intro-grounding-gemini.ipynb

def grounding_response_with_citations_original(response: GenerationResponse):
    """Prints Gemini response with grounding citations."""
    grounding_metadata = response.candidates[0].grounding_metadata

    # Citation indices are in byte units
    ENCODING = "utf-8"
    text_bytes = response.text.encode(ENCODING)

    prev_index = 0
    markdown_text = ""

    for grounding_support in grounding_metadata.grounding_supports:
        text_segment = text_bytes[
            prev_index : grounding_support.segment.end_index
        ].decode(ENCODING)

        footnotes_text = ""
        for grounding_chunk_index in grounding_support.grounding_chunk_indices:
            footnotes_text += f"[{grounding_chunk_index + 1}]"

        markdown_text += f"{text_segment} {footnotes_text}\n"
        prev_index = grounding_support.segment.end_index

    if prev_index < len(text_bytes):
        markdown_text += str(text_bytes[prev_index:], encoding=ENCODING)

    markdown_text += "### Relevante Quellen\n"

    for index, grounding_chunk in enumerate(
        grounding_metadata.grounding_chunks, start=1
    ):
        context = grounding_chunk.web or grounding_chunk.retrieved_context
        if not context:
            print(f"Skipping Grounding Chunk {grounding_chunk}")
            continue

        markdown_text += f"{index}. [{context.title}]({context.uri})\n"

    return markdown_text

def grounding_response_with_citations(response: GenerationResponse) -> str:
    """Prints Gemini response with grounding citations."""
    grounding_metadata = response.candidates[0].grounding_metadata

    # Citation indices are in byte units
    ENCODING = "utf-8"
    text_bytes = response.text.encode(ENCODING)

    prev_index = 0
    markdown_text = ""

    for grounding_support in grounding_metadata.grounding_supports:
        text_segment = text_bytes[
            prev_index : grounding_support.segment.end_index
        ].decode(ENCODING)

        footnotes_text = ""
        for grounding_chunk_index in grounding_support.grounding_chunk_indices:
            footnotes_text += f"[{grounding_chunk_index + 1}]"

        markdown_text += f"{text_segment} {footnotes_text}\n"
        prev_index = grounding_support.segment.end_index

    if prev_index < len(text_bytes):
        markdown_text += str(text_bytes[prev_index:], encoding=ENCODING)

    markdown_text += "### Relevante Quellen\n"

    already_used_citations = []

    for grounding_support in response.candidates[0].grounding_metadata.grounding_supports:
        for grounding_chunk_index in grounding_support.grounding_chunk_indices:
            for index, grounding_chunk in enumerate(
                response.candidates[0].grounding_metadata.grounding_chunks
            ):
                context = grounding_chunk.web or grounding_chunk.retrieved_context
                if not context:
                    continue

                if grounding_chunk_index == index:
                    if index not in already_used_citations:
                        folder_path = "/".join(str(context.uri).split("/")[3:]) + "/"
                        markdown_text += f"[{(index + 1)}] [{folder_path}] \n \n"
                        already_used_citations.append(index)

    return markdown_text
