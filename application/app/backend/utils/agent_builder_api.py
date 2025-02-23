from typing import List, Dict
from google.cloud.discoveryengine_v1beta import (
    SearchRequest,
    SearchServiceClient
)
from google.cloud.discoveryengine_v1beta.services.search_service import pagers
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine


def _init_search_client(project: str, location: str, datastore_id: str):
    """
    Initialisiert den Suchclient und die Serving-Konfiguration.

    Args:
        project: Google Cloud Projekt-ID.
        location: Standort des Datenspeichers.
        datastore_id: ID des Datenspeichers.

    Returns:
        Ein Tupel aus dem SearchServiceClient und dem Serving-Konfigurationspfad.
    """
    client_options = (
        ClientOptions(
            api_endpoint=f"{location}-discoveryengine.googleapis.com")
    )

    search_client = SearchServiceClient(client_options=client_options)

    serving_config = search_client.serving_config_path(
        project=project,
        location=location,
        data_store=datastore_id,
        serving_config="default_config",
    )

    return search_client, serving_config


def _init_search_behavior(result_count: int) -> SearchRequest:
    """Initialisiert das Suchverhalten.

    Args:
        result_count: Die Anzahl der zurückzugebenden Ergebnisse.

    Returns:
        Eine SearchRequest-Instanz mit der konfigurierten Inhaltsuche.
    """
    summary_spec = SearchRequest.ContentSearchSpec.SummarySpec(
        summary_result_count=result_count,
        include_citations=True,
    )

    content_spec = SearchRequest.ContentSearchSpec(
        summary_spec=summary_spec
    )

    return content_spec


def _search_data_store(
    search_client: SearchServiceClient,
    serving_config: str,
    content_spec: SearchRequest,
    search_query: str
) -> pagers.SearchPager:
    """Durchsucht den Datenspeicher nach der angegebenen Suchanfrage.

    Args:
        search_client: Der SearchServiceClient.
        serving_config: Der Pfad zur Serving-Konfiguration.
        content_spec: Die ContentSearchSpec-Instanz.
        search_query: Die Suchanfrage.

    Returns:
        Die Suchergebnisse als String.
    """
    search_request = SearchRequest(
        serving_config=serving_config,
        query=search_query,
        page_size=5,
        content_search_spec=content_spec
    )

    result = search_client.search(
        request=search_request
    )

    return result


def _process_result(search_result: str) -> str:
    """Verarbeitet das Suchergebnis und gibt eine Antwortzeichenfolge zurück.

    Args:
        search_result: Das Suchergebnis als String.

    Returns:
        Eine Antwortzeichenfolge mit Zusammenfassung und relevanten Ressourcen.
    """
    # build the response text
    summary = search_result.summary
    # 1. get all used references (indexes)
    used_reference_indexes = set()
    for citation in summary.summary_with_metadata.citation_metadata.citations:
        for source in citation.sources:
            try:
                used_reference_indexes.add(source.reference_index)
            except AttributeError:
                used_reference_indexes.add(0)

    # get the references
    doc_links = set()
    for ref_id in list(used_reference_indexes):
        used_document = search_result.results[ref_id].document
        # get the original document name
        document_name = used_document.derived_struct_data.get("link")
        # extract the link from the name
        document_link = document_name.rsplit(
            "/", 1)[1].replace("<>", "/").rsplit(".", 1)[0]
        doc_links.add(document_link)

    references_text = "\n- ".join(list(doc_links)) if len(doc_links) > 0 else None
    summary_text = summary.summary_with_metadata.summary if summary.summary_with_metadata.summary else summary.summary_text

    answer = f"{summary_text}\n\nRelevante Ressourcen:\n- {references_text}" if references_text else summary_text

    return answer


def search_engine(search_query: str, process_string: bool, project: str, location: str, datastore_id: str):
    search_client, serving_config = _init_search_client(project=project,
                                                    location=location,
                                                    datastore_id=datastore_id)

    content_spec = _init_search_behavior(result_count=5)

    result = _search_data_store(search_client=search_client,
                            serving_config=serving_config,
                            content_spec=content_spec,
                            search_query=search_query)

    summary = (_process_result(search_result=result) if process_string else str(result.summary))

    return summary

from typing import List



def multi_turn_search(
    project_id: str,
    location: str,
    datastore_id: str,
    search_queries: List[str],
) -> List[discoveryengine.ConverseConversationResponse]:
    #  For more information, refer to:
    # https://cloud.google.com/generative-ai-app-builder/docs/locations#specify_a_multi-region_for_your_data_store
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
    )

    # Create a client
    client = discoveryengine.ConversationalSearchServiceClient(
        client_options=client_options
    )

    # Initialize Multi-Turn Session
    conversation = client.create_conversation(
        parent=client.data_store_path(
            project=project_id, location=location, data_store=datastore_id
        ),
        conversation=discoveryengine.Conversation(),
    )

    responses = []
    for search_query in search_queries:
        # Add new message to session
        request = discoveryengine.ConverseConversationRequest(
            name=conversation.name,
            query=discoveryengine.TextInput(input=search_query),
            serving_config=client.serving_config_path(
                project=project_id,
                location=location,
                data_store=datastore_id,
                serving_config="default_config",
            ),
            # Options for the returned summary
            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=3,
                include_citations=True,
            ),
        )
        response = client.converse_conversation(request)
        responses.append(response)

    return responses




def process_multiturn_response(response: List[str]) -> List[Dict]:
    replies_list = []
    i = 0
    for reply in response:
        answer = reply.reply.summary.summary_text
        prompt = reply.conversation.messages[i].user_input.input
        references_list = reply.reply.summary.summary_with_metadata.citation_metadata.citations
        i = i + 2
        citations_reference_indices = []
        for reference in references_list:
            sources = reference.sources

            for source in sources:
                citations_reference_indices.append(source.reference_index)
        # print("CITATION INDICES", citations_reference_indices)
        citations_reference_indices_uniques = list(set(citations_reference_indices))

        reference_ids = []
        for citation_index in citations_reference_indices_uniques:
            reference = reply.reply.summary.summary_with_metadata.references[citation_index]
            reference_id = (str(reference.document)).split("/")[-1]
            reference_ids.append({
                "reference_id": reference_id,
                "citation_id": citation_index
            })

        # print("REFERENCE IDs", reference_ids)
        reference_objects = []
        for reference in reference_ids:
            search_results = reply.search_results
            for search_result in search_results:
                if reference["reference_id"] == search_result.id:

                    # extractive_answers = search_result.document.derived_struct_data["extractive_answers"]
                    extractive_answers = search_result.document.derived_struct_data.get("extractive_answers", [])
                    citation_contents = []

                    for extractive_answer in extractive_answers:
                        citation_content = {}
                        if "pageNumber" in extractive_answer:
                            citation_content["page_number"] = extractive_answer["pageNumber"]
                        else:
                            citation_content["page_number"] = 999
                        if "content" in extractive_answer:
                            citation_content["ground_content"] = extractive_answer["content"]
                        else:
                            citation_content["ground_content"] = "Kein Inhalt erhalten"
                        citation_contents.append(citation_content)

                    metadata_obj = {
                        "reference_id": reference["reference_id"],
                        "citation_id": reference["citation_id"] + 1,
                        "file_path": search_result.document.struct_data["path_in_dir"],
                        "file_name": search_result.document.struct_data["file_name"],
                        "sharepoint_url": search_result.document.struct_data["sharepoint_url"],
                        "citation_contents": citation_contents,
                    }
                    reference_objects.append(metadata_obj)

        replies_list.append({
            "prompt": prompt,
            "answer": answer,
            "references": reference_objects
        })
    return replies_list

def create_markdown(answer_with_quotes: Dict):
    markdown_text = answer_with_quotes["answer"] # + "\n \n"+ "#### Relevante Quellen \n"
    return markdown_text
