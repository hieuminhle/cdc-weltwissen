import os
import uvicorn
import sys
import logging
import json

from fastapi import FastAPI, Response, Request
from fastapi.logger import logger
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.resolve()))
from backend.utils import (vertexai_api,
                           dlp_api,
                           storage_api,
                           sql_api,
                           agent_builder_api,
                           data_processing,
                           constants)
from backend.schemas.schemas import(Answer,
                                    ImageAnswer,
                                    Question,
                                    HealthCheck,
                                    UnhealthyCheck,
                                    DocQuestion,
                                    BackendError,
                                    Conversation,
                                    ImageConversation,
                                    ImageQuestion,
                                    ProvidedDocQuestion,
                                    AnswerWithQuotes,
                                    GroundContent,
                                    Citation,
                                    ExcelProcessed,
                                    FileBytes)
from google.api_core.exceptions import ResourceExhausted


PROJECT_ID = os.environ["PROJECT_ID"]
DATASTORE_LOCATION = os.environ["DATASTORE_LOCATION"]
DATASTORE_ID = os.environ["DATASTORE_ID"]

app = FastAPI()

@app.post("/llm/provideddocchat",response_model=Answer)
def call_llm_provided(request: Request, question: ProvidedDocQuestion):
    logging.basicConfig(level=logging.INFO)
    available_regions = ["europe-west3", "europe-west4", "europe-west1", "europe-west9"] # EU only, here: Frankfurt, Netherlands, Belgium, Paris
    try:
        doc_question = question.doc_question
        session_id = question.session_id
        history = question.history
        oid_hashed = question.oid_hashed

        dlp_response = dlp_api.inspect_prompt(
            prompt = doc_question,
            project_id = PROJECT_ID
        )

        doc_context = ""

        doc_key = question.doc_key
        doc_map = {
            "fragenkatalog":"/local_files/fragenkatalogv2.txt",
            "strategiepapier":"/local_files/strategie_final_short.txt",
        }
        script_dir_name = os.path.dirname(os.path.realpath(__file__))
        with open(f"{script_dir_name}{doc_map[doc_key]}", "r") as f:
            lines = f.readlines()
            doc_context = "\n".join(lines)

        system_instruction = ""
        if doc_key == "fragenkatalog":
            system_instruction = constants.SYSTEM_INSTRUCTION_GEMINI_KATALOG
        elif doc_key == "strategiepapier":
            system_instruction = constants.SYSTEM_INSTRUCTION_GEMINI_STRATEGIE

        quota_exceeded = False

        # all vars for return type (default values) / except question and history
        errors = []
        full_answer = ""

        # Sets default values for logging as these values are not provided in case DLP finds PII. -1 in the logging SQL table means that DLP findings > 0.
        num_token_prompt = -1
        num_token_response = -1
        response_time = -1

        if dlp_response["num_findings"] > 0:
            full_answer = dlp_response["findings_formatted"]
            errors.append(BackendError(
                code="500",
                msg=full_answer,
                status="DLP_ERROR"
            ))
        else:
            for region in available_regions:
                try:
                    result, response_time = vertexai_api.ask_gemini_docchat_question(
                        doc_context=doc_context,
                        prompt=question.doc_question,
                        project_id=PROJECT_ID,
                        history=question.history,
                        model_name=constants.GEMINI_TEXT_CHAT_DEFAULT_MODEL_NAME,
                        system_instruction=system_instruction,
                        temperature=1.0,
                        max_output_tokens=500,
                        location=region,
                    )
                    full_answer, num_token_prompt, num_token_response = result
                    quota_exceeded = False
                    break
                except ResourceExhausted as re:
                    logger.warning(re)
                    quota_exceeded = True
                    continue
        if quota_exceeded:
            full_answer = constants.QUOTA_EXCEEDED_ERROR
            errors.append(BackendError(
                code="500",
                msg=full_answer,
                status="QUOTA_ERROR"
            ))

        history.append(Conversation(
          question=question.doc_question,
          answer=full_answer
        ))

        storage_api.log_history(
            session_id,
            oid_hashed,
            "provided_doc_chat",
            history,
            os.environ["CHATBOT_LOGGING_BUCKET"],
            doc_context,
       )

        sql_api.log_usage(oid_hashed=oid_hashed, session_id=session_id, chat_type="provided_doc_chat", num_token_prompt=num_token_prompt, num_token_response=num_token_response, response_time=response_time)

        logger.info(f"\nNutzerfrage: {question.doc_question}\nAntwort: {full_answer}")

        return Answer(
            question=question.doc_question,
            answer=full_answer,
            history = history,
            errors=errors,
            info = ""
        )
    except Exception as ex:
        logger.exception("CDC-GenAI-Weltwissen-Backend-Docchat-Error: %s", ex)
        return Response(
            content=str(ex),
            status_code=500
        )

@app.post("/llm/docchat",response_model=Answer)
def call_llm(request: Request, question: DocQuestion):
    logging.basicConfig(level=logging.INFO)
    available_regions = ["europe-west3", "europe-west4", "europe-west1", "europe-west9"] # EU only, here: Frankfurt, Netherlands, Belgium, Paris
    try:
        doc_context = question.doc_context
        doc_question = question.doc_question
        session_id = question.session_id
        oid_hashed = question.oid_hashed
        history = question.history

        dlp_response = dlp_api.inspect_prompt(
            prompt=doc_question,
            project_id=PROJECT_ID
        )
        dlp_response_doc, dlp_info, dlp_error = dlp_api.anonymize_text(
            doc_content=doc_context,
            project_id=PROJECT_ID,
        )

        quota_exceeded = False

        # all vars for return type (default values) / except question and history
        errors = []
        full_answer = ""

        # Sets default values for logging as these values are not provided in case DLP finds PII. -1 in the logging SQL table means that DLP findings > 0.
        num_token_prompt = -1
        num_token_response = -1
        response_time = -1

        if dlp_response["num_findings"] > 0:
            full_answer = dlp_response["findings_formatted"]
            errors.append(BackendError(
                code="500",
                msg=full_answer,
                status="DLP_ERROR"
            ))
        elif dlp_error:
            errors.append(dlp_error)
        else:
            for region in available_regions:
                try:
                    result, response_time = vertexai_api.ask_gemini_docchat_question(
                        doc_context=dlp_response_doc,
                        prompt=question.doc_question,
                        project_id=PROJECT_ID,
                        history=question.history,
                        model_name=constants.GEMINI_TEXT_CHAT_DEFAULT_MODEL_NAME,
                        location=region,
                    )
                    full_answer, num_token_prompt, num_token_response = result
                    quota_exceeded = False
                    break
                except ResourceExhausted as re:
                    logger.warning(re)
                    quota_exceeded = True
                    continue
        if quota_exceeded:
            full_answer = constants.QUOTA_EXCEEDED_ERROR
            errors.append(BackendError(
                code="500",
                msg=full_answer,
                status="QUOTA_ERROR"
            ))

        history.append(Conversation(
          question=question.doc_question,
          answer=full_answer
        ))

        storage_api.log_history(
            session_id,
            oid_hashed,
            "doc_chat",
            history,
            os.environ["CHATBOT_LOGGING_BUCKET"],
            doc_context,
       )

        sql_api.log_usage(oid_hashed=oid_hashed, session_id=session_id, chat_type="doc_chat", num_token_prompt=num_token_prompt, num_token_response=num_token_response, response_time=response_time)

        logger.info(f"\nNutzerfrage: {question.doc_question}\nAntwort: {full_answer}")

        return Answer(
            question=question.doc_question,
            answer=full_answer,
            history = history,
            errors=errors,
            info = dlp_info
        )
    except Exception as ex:
        logger.exception("CDC-GenAI-Weltwissen-Backend-Docchat-Error: %s", ex)
        return Response(
            content=str(ex),
            status_code=500
        )

@app.post("/llm/textchat", response_model=Answer)
def call_llm(request: Request, question: Question):
    logging.basicConfig(level=logging.INFO)
    available_regions = ["europe-west3", "europe-west4", "europe-west1", "europe-west9"] # EU only, here: Frankfurt, Netherlands, Belgium, Paris
    try:
        history = question.history # Is logged in Cloud Storage Bucket
        session_id = question.session_id
        oid_hashed = question.oid_hashed
        apply_pseudonymization = question.apply_pseudonymization

        if apply_pseudonymization:
            # Pseudonymize the prompt to replace PII before sending it to LLM
            pseudonymized_prompt, replacement_mapping, dlp_error = dlp_api.pseudonymize_text(prompt=question.question, project_id=PROJECT_ID)
            # Inspect whether the user prompt contains at personal sensitive information
        dlp_response = dlp_api.inspect_prompt(
            prompt=question.question,
            project_id=PROJECT_ID,
        )
        quota_exceeded = False

        # all vars for return type (default values) / except question and history
        errors = []
        full_answer = ""

        # Sets default values for logging as these values are not provided in case DLP finds PII. -1 in the logging SQL table means that DLP findings > 0.
        num_token_prompt = -1
        num_token_response = -1
        response_time = -1

        if dlp_response["num_findings"] > 0 and apply_pseudonymization == False:
            full_answer = dlp_response["findings_formatted"]
            errors.append(BackendError(
                code="500",
                msg=full_answer,
                status="DLP_ERROR"
            ))
        else:
            for region in available_regions:
                try:
                    result, response_time = vertexai_api.ask_gemini_textchat_question(
                        prompt=question.question if not apply_pseudonymization else pseudonymized_prompt,
                        project_id=PROJECT_ID,
                        history=question.history,
                        location=region
                    ) # Try to get an answer from the Vertex AI PaLM API endpoint. If the quota for that API is exceeded in this region the for-loop continues with the next region in the list defined above.

                    full_answer, num_token_prompt, num_token_response = result
                    quota_exceeded = False
                    break
                except Exception as e:
                    logger.error(str(e))
                    print(e)
                except ResourceExhausted as re:
                    logger.warning(re)
                    quota_exceeded = True
                    continue

        if quota_exceeded:
            full_answer = constants.QUOTA_EXCEEDED_ERROR
            errors.append(BackendError(
                code="500",
                msg=full_answer,
                status="QUOTA_ERROR"
            ))

        history.append(Conversation(
          question=question.question,
          answer=full_answer
        ))

        storage_api.log_history(
            session_id,
            oid_hashed,
            "text_chat",
            history,
            os.environ["CHATBOT_LOGGING_BUCKET"],
        )

        sql_api.log_usage(oid_hashed=oid_hashed, session_id=session_id, chat_type="text_chat", num_token_prompt=num_token_prompt, num_token_response=num_token_response, response_time=response_time)


        logger.info(f"\nNutzerfrage: {question.question}\nAntwort: {full_answer}")
        return Answer(
            question = question.question,
            answer = full_answer,
            history = history,
            errors = errors
        )
    except Exception as ex:
        logger.exception("CDC-GenAI-Weltwissen-Backend-Textchat-Error: %s", ex)
        return Response(content=str(ex), status_code=500)



@app.post("/llm/codechat", response_model=Answer)
def call_llm(request: Request, question: Question):
    logging.basicConfig(level=logging.INFO)
    available_regions = ["europe-west3", "europe-west4", "europe-west1", "europe-west9"] # EU only, here: Frankfurt, Netherlands, Belgium, Paris
    try:
        history = question.history
        session_id = question.session_id
        oid_hashed = question.oid_hashed

        # Inspect whether the user prompt contains at personal sensitive information
        dlp_response = dlp_api.inspect_prompt(
            prompt=question.question,
            project_id=PROJECT_ID,
        )

        quota_exceeded = False

        # all vars for return type (default values) / except question and history
        errors = []
        full_answer = ""

        # Sets default values for logging as these values are not provided in case DLP finds PII. -1 in the logging SQL table means that DLP findings > 0.
        num_token_prompt = -1
        num_token_response = -1
        response_time = -1

        if dlp_response["num_findings"] > 0:
            full_answer = dlp_response["findings_formatted"]
            errors.append(BackendError(
                code="500",
                msg=full_answer,
                status="DLP_ERROR"
            ))
        else:
            for region in available_regions:
                try:
                    result, response_time = vertexai_api.ask_codechat_question(
                        prompt=question.question,
                        project_id=PROJECT_ID,
                        history=question.history,
                        location=region
                    ) # Try to get an answer from the Vertex AI PaLM API endpoint. If the quota for that API is exceeded in this region the for-loop continues with the next region in the list defined above.

                    full_answer, num_token_prompt, num_token_response = result
                    quota_exceeded = False
                    break
                except ResourceExhausted as re:
                    logger.warning(re)
                    quota_exceeded = True
                    continue
        if quota_exceeded:
            full_answer = constants.QUOTA_EXCEEDED_ERROR
            errors.append(BackendError(
                code="500",
                msg=full_answer,
                status="QUOTA_ERROR"
            ))

        history.append(Conversation(
          question=question.question,
          answer=full_answer
        ))

        storage_api.log_history(
            session_id,
            oid_hashed,
            "code_chat",
            history,
            os.environ["CHATBOT_LOGGING_BUCKET"],
        )

        sql_api.log_usage(oid_hashed=oid_hashed, session_id=session_id, chat_type="code_chat", num_token_prompt=num_token_prompt, num_token_response=num_token_response, response_time=response_time)

        logger.info(f"\nNutzerfrage: {question.question}\nAntwort: {full_answer}")
        return Answer(
            question = question.question,
            answer = full_answer,
            history = history,
            errors = errors
        )
    except Exception as ex:
        logger.exception("CDC-GenAI-Weltwissen-Backend-Codechat-Error: %s", ex)
        return Response(content=str(ex), status_code=500)

@app.post("/llm/imagen", response_model=ImageAnswer)
def call_llm(request: Request, question: ImageQuestion):
    logging.basicConfig(level=logging.INFO)
    available_regions = ["europe-west3", "europe-west4", "europe-west1", "europe-west9"] # EU only, here: Frankfurt, Netherlands, Belgium, Paris
    try:
        history = question.history
        session_id = question.session_id
        oid_hashed = question.oid_hashed

        # Inspect whether the user prompt contains at personal sensitive information
        dlp_response = dlp_api.inspect_prompt(
            prompt=question.question,
            project_id=PROJECT_ID,
        )

        quota_exceeded = False

        # all vars for return type (default values) / except question and history
        errors = []
        image_urls = []
        en_prompt = ""
        full_answer = ""
        question_translated = ""
        answer_urls: list = []

        # Sets default values for logging as these values are not provided in case DLP finds PII. -1 in the logging SQL table means that DLP findings > 0.
        num_token_prompt = -1
        num_token_response = -1
        response_time = -1

        if dlp_response["num_findings"] > 0:
            full_answer = dlp_response["findings_formatted"]
            errors.append(BackendError(
                code="500",
                msg=full_answer,
                status="DLP_ERROR"
            ))
        else:
            for region in available_regions:
                try:
                    result, response_time = vertexai_api.generate_image(
                        prompt=question.question,
                        project_id=PROJECT_ID,
                        history=[],
                        location=region,
                        session_id=session_id) # Try to get an answer from the Vertex AI PaLM API endpoint. If the quota for that API is exceeded in this region the for-loop continues with the next region in the list defined above.

                    image_urls, en_prompt, errors = result

                    quota_exceeded = False
                    question_translated = en_prompt
                    answer_urls: list = image_urls
                    full_answer = f"Übersetzter Englischer Prompt: {en_prompt}\nCloud Storage URLs: {image_urls}"
                    break
                except ResourceExhausted as re:
                    logger.warning(re)
                    quota_exceeded = True
                    continue

        if quota_exceeded:
            full_answer = constants.QUOTA_EXCEEDED_ERROR
            errors.append(BackendError(
                code="500",
                msg=full_answer,
                status="QUOTA_ERROR"
            ))
        elif len(image_urls) == 0:
            full_answer = constants.IMAGE_CHAT_EMPTY_LIST_ERROR
            errors.append(BackendError(
                code="500",
                msg=full_answer,
                status="EMPTY_IMAGE_RESPONSE"
            ))

        history.append(
            ImageConversation(
              question=question.question,
              question_translated=question_translated,
              answer_urls=answer_urls,
            )
        )

        storage_api.log_history(
            session_id,
            oid_hashed,
            "image_chat",
            history,
            os.environ["CHATBOT_LOGGING_BUCKET"],
        )

        sql_api.log_usage(oid_hashed=oid_hashed, session_id=session_id, chat_type="image_chat", num_token_prompt=None, num_token_response=None, response_time=response_time)


        logger.info(f"\nNutzerfrage: {question.question}\nAntwort: {full_answer}")
        return ImageAnswer(
            original_prompt = question.question,
            en_prompt = en_prompt,
            images = image_urls,
            history = history,
            errors = errors
        )
    except Exception as ex:
        logger.exception("CDC-GenAI-Weltwissen-Backend-Imagen-Error: %s", ex)
        return Response(content=str(ex), status_code=500)


@app.post("/agent-builder/query-datastore", response_model=Answer)
def call_datastore(request: Request, question: Question):
    logging.basicConfig(level=logging.INFO)
    # EU only, here: Frankfurt, Netherlands, Belgium, Paris
    available_regions = ["europe-west3",
                         "europe-west4", "europe-west1", "europe-west9"]
    try:
        history = question.history
        session_id = question.session_id
        oid_hashed = question.oid_hashed

        # Inspect whether the user prompt contains at personal sensitive information
        dlp_response = dlp_api.inspect_prompt(
            prompt=question.question,
            project_id=PROJECT_ID,
        )

        quota_exceeded = False

        # all vars for return type (default values) / except question and history
        errors = []
        full_answer = ""

        # Sets default values for logging as these values are not provided in case DLP finds PII. -1 in the logging SQL table means that DLP findings > 0.
        num_token_prompt = -1
        num_token_response = -1
        response_time = -1

        if dlp_response["num_findings"] > 0:
            full_answer = dlp_response["findings_formatted"]
            errors.append(BackendError(
                code="500",
                msg=full_answer,
                status="DLP_ERROR"
            ))
        else:
            try:
                result = agent_builder_api.search_engine(
                    project=PROJECT_ID,
                    search_query=question.question,
                    process_string=False,
                    location=DATASTORE_LOCATION,
                    datastore_id=DATASTORE_ID
                )

                # full_answer, num_token_prompt, num_token_response = result
                quota_exceeded = False
            except ResourceExhausted as re:
                logger.warning(re)
                quota_exceeded = True
        if quota_exceeded:
            full_answer = constants.QUOTA_EXCEEDED_ERROR
            errors.append(BackendError(
                code="500",
                msg=full_answer,
                status="QUOTA_ERROR"
            ))

        history.append(Conversation(
            question=question.question,
            answer=full_answer
        ))

        storage_api.log_history(
            session_id,
            oid_hashed,
            "code_chat",
            history,
            os.environ["CHATBOT_LOGGING_BUCKET"],
        )

        sql_api.log_usage(oid_hashed=oid_hashed, session_id=session_id, chat_type="bafin_chat", num_token_prompt=num_token_prompt, num_token_response=num_token_response, response_time=response_time)

        logger.info(f"\nNutzerfrage: {question.question}\nAntwort: {result}")
        return Answer(
            question=question.question,
            answer=result,
            history=history,
            errors=errors
        )
    except Exception as ex:
        logger.exception("CDC-GenAI-Weltwissen-Backend-Codechat-Error: %s", ex)
        return Response(content=str(ex), status_code=500)


@app.post("/agent-builder/bafin-grounded-response", response_model=Answer)
def call_bafin_docs(request: Request, question: Question):
    logging.basicConfig(level=logging.INFO)
    # EU only, here: Frankfurt, Netherlands, Belgium, Paris
    available_regions = ["europe-west3",
                         "europe-west4", "europe-west1", "europe-west9"]
    try:
        history = question.history
        session_id = question.session_id
        oid_hashed = question.oid_hashed

        # Inspect whether the user prompt contains at personal sensitive information
        dlp_response = dlp_api.inspect_prompt(
            prompt=question.question,
            project_id=PROJECT_ID,
        )

        quota_exceeded = False

        # all vars for return type (default values) / except question and history
        errors = []
        full_answer = ""

        # Sets default values for logging as these values are not provided in case DLP finds PII. -1 in the logging SQL table means that DLP findings > 0.
        num_token_prompt = -1
        num_token_response = -1
        response_time = -1

        if dlp_response["num_findings"] > 0:
            full_answer = dlp_response["findings_formatted"]
            errors.append(BackendError(
                code="500",
                msg=full_answer,
                status="DLP_ERROR"
            ))
        else:
            for region in available_regions:
                try:
                    result = vertexai_api.ask_gemini_with_bafin_docs(
                        project_id=PROJECT_ID,
                        prompt=question.question,
                        datastore_id=DATASTORE_ID,
                        history=question.history
                    )

                    full_answer, num_token_prompt, num_token_response = result
                    quota_exceeded = False
                    break
                except ResourceExhausted as re:
                    logger.warning(re)
                    quota_exceeded = True
                    continue
        if quota_exceeded:
            full_answer = constants.QUOTA_EXCEEDED_ERROR
            errors.append(BackendError(
                code="500",
                msg=full_answer,
                status="QUOTA_ERROR"
            ))

        history.append(Conversation(
            question=question.question,
            answer=full_answer
        ))

        storage_api.log_history(
            session_id,
            oid_hashed,
            "bafin_chat",
            history,
            os.environ["CHATBOT_LOGGING_BUCKET"],
        )

        sql_api.log_usage(oid_hashed=oid_hashed, session_id=session_id, chat_type="bafin_chat", num_token_prompt=num_token_prompt, num_token_response=num_token_response, response_time=response_time)

        logger.info(f"\nNutzerfrage: {question.question}\nAntwort: {full_answer}")
        return Answer(
            question=question.question,
            answer=full_answer,
            history=history,
            errors=errors
        )
    except Exception as ex:
        logger.exception("CDC-GenAI-Weltwissen-Backend-BafinChat-Error: %s", ex)
        return Response(content=str(ex), status_code=500)


@app.post("/agent-builder/bafin-multiturn-discovery-engine", response_model=AnswerWithQuotes)
def call_bafin_multiturn(request: Request, question: Question):
    logging.basicConfig(level=logging.INFO)
    # EU only, here: Frankfurt, Netherlands, Belgium, Paris
    available_regions = ["europe-west3",
                         "europe-west4", "europe-west1", "europe-west9"]
    try:
        history = question.history
        session_id = question.session_id
        oid_hashed = question.oid_hashed

        # Inspect whether the user prompt contains at personal sensitive information
        dlp_response = dlp_api.inspect_prompt(
            prompt=question.question,
            project_id=PROJECT_ID,
        )

        quota_exceeded = False

        # all vars for return type (default values) / except question and history
        errors = []
        full_answer = ""

        # Sets default values for logging as these values are not provided in case DLP finds PII. -1 in the logging SQL table means that DLP findings > 0.
        num_token_prompt = -1
        num_token_response = -1
        response_time = -1

        if dlp_response["num_findings"] > 0:
            full_answer = dlp_response["findings_formatted"]
            errors.append(BackendError(
                code="500",
                msg=full_answer,
                status="DLP_ERROR"
            ))
        else:
            try:
                result = agent_builder_api.multi_turn_search(
                    project_id=PROJECT_ID,
                    datastore_id=DATASTORE_ID,
                    location=DATASTORE_LOCATION,
                    search_queries=[question.question],
                )

                full_answer = agent_builder_api.process_multiturn_response(response=result)

                citations = []
                for reference in full_answer[-1]["references"]:
                    ground_content = []
                    # print(reference)
                    for content in reference["citation_contents"]:
                        ground_content.append(
                            GroundContent(
                                page=content["page_number"],
                                content=content["ground_content"]
                            )
                        )

                    citations.append(
                        Citation(
                            id=reference["citation_id"],
                            name=reference["file_name"],
                            link=reference["sharepoint_url"],
                            path=reference["file_path"],
                            content=ground_content
                    ))

                quota_exceeded = False
            except ResourceExhausted as re:
                logger.warning(re)
                quota_exceeded = True
        if quota_exceeded:
            full_answer = constants.QUOTA_EXCEEDED_ERROR
            errors.append(BackendError(
                code="500",
                msg=full_answer,
                status="QUOTA_ERROR"
            ))

        history.append(Conversation(
            question=question.question,
            answer=full_answer[-1]["answer"]
        ))

        storage_api.log_history(
            session_id,
            oid_hashed,
            "bafin_chat",
            history,
            os.environ["CHATBOT_LOGGING_BUCKET"],
        )

        sql_api.log_usage(oid_hashed=oid_hashed, session_id=session_id, chat_type="bafin_chat", num_token_prompt=num_token_prompt, num_token_response=num_token_response, response_time=response_time)

        logger.info(f"\nNutzerfrage: {question.question}\nAntwort: {full_answer}")
        return AnswerWithQuotes(
            question=question.question,
            answer=agent_builder_api.create_markdown(full_answer[-1]),
            citations=citations,
            history=history,
            errors=errors
        )
    except Exception as ex:
        logger.exception("CDC-GenAI-Weltwissen-Backend-BafinChat-Error: %s", ex)
        return Response(content=str(ex), status_code=500)


@app.post("/excel_processing", response_model=ExcelProcessed)
def process_excel(request: Request, file_bytes: FileBytes):
    logging.basicConfig(level=logging.INFO)
    try:
        table_data = data_processing.process_excel_bytes(bytes=file_bytes)
        return ExcelProcessed(table_data=table_data)
    except Exception as ex:
        logger.exception("CDC-GenAI-Weltwissen-Backend-Excel-Processing-Error: %s", ex)
        return Response(content=str(ex), status_code=500)


# Health endpoint for startup/health checks
@app.get("/health", status_code=200, response_model=HealthCheck)
def get_health():
    return HealthCheck(status="OK")

@app.get("/unhealthy",status_code=500,response_model=UnhealthyCheck)
def get_unhealthy():
    return UnhealthyCheck(status="Really not okay!")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8003)
