import logging
from collections.abc import Sequence
from typing import List

from google.cloud.dlp_v2 import DlpServiceClient, InspectContentRequest, Finding
from google.cloud.dlp_v2.types import Finding
from faker import Faker
import gender_guesser.detector as gender_detector

from . import constants
from backend.schemas.schemas import BackendError

logger = logging.getLogger(__name__)
client = DlpServiceClient()
fake = Faker("de_DE")
detector = gender_detector.Detector()

def _call_dlp_api(prompt: str, project_id: str):
    request = InspectContentRequest(
        inspect_config={
            "info_types": [{"name": info_type} for info_type in constants.DEFAULT_INFO_TYPES],
            "min_likelihood": constants.DEFAULT_MIN_LIKELIHOOD,
            "include_quote": True,
            "limits": {"max_findings_per_request": constants.DEFAULT_MAX_FINDINGS},
        },
        parent=f"projects/{project_id}/locations/europe-west3",
        item={"value": prompt},
    )

    response = client.inspect_content(
        request=request,
    )
    logger.info(response)
    return response


def _split_prompt(prompt: str, max_len: int = constants.MAX_PROMPT_SIZE_DLP):
    """Splits a string into sections with a maximum length.

    Args:
        prompt (str): The string to be split.
        max_len (int): The maximum length of the sections.

    Returns:
        A list of the sections.
    """
    return [prompt[i:i + max_len] for i in range(0, len(prompt), max_len)]


def _anonymize_text_section(text: str, findings: List[Finding]) -> str:
    """Anonymizes a text section based on the results of the DLP API.

    Args:
        text (str): The text to be anonymized.
        findings (List[Finding]): A list of "Finding" objects, containing information about sensitive data locations within the text.

    Returns:
        str: The anonymized text with sensitive information replaced by asterisks.
    """
    out_text = text
    for finding in findings:
        start = finding.location.codepoint_range.start
        end = finding.location.codepoint_range.end
        out_text = out_text[:start] + "*" * (end - start) + out_text[end:]
    return out_text

def pseudonymize_text(prompt: str, project_id: str) -> tuple[str, dict, BackendError]:
    """Pseudonymizes the given text and returns the pseudomized text and the mapping of original and pseudonymized values.

    This method pseudonymizes the provided text using the Google Cloud DLP API and the Faker library.

    Args:
        prompt: The text to be pseudonymized.
        project_id: The project ID of the Google Cloud project.

    Returns:
        A tuple containing:
            - The pseudonymized text.
            - A dictionnary with pseudonymization mapping.
            - A BackendError object if an error occurred, otherwise None.
    """
    try:
        replacement_mapping = {}
        response = _call_dlp_api(prompt, project_id)
        for finding in response.result.findings:
            match finding.info_type.name:
                case "FIRST_NAME":
                    gender = detector.get_gender(finding.quote)
                    if gender in ["female", "mostly_female"]:
                        replacement = fake.first_name_female()
                    elif gender in ["male", "mostly_male"]:
                        replacement = fake.first_name_male()
                    else:
                        replacement = fake.first_name_nonbinary()
                case "LAST_NAME":
                    replacement = fake.last_name()
                case "STREET_ADDRESS":
                    replacement = fake.address().replace("\n",", ")
                case "PHONE_NUMBER":
                    replacement = fake.phone_number()
            prompt = prompt.replace(finding.quote, replacement)
            #replacement_mapping[replacement] = [finding.quote, finding.info_type.name]
            replacement_mapping[finding.info_type.name] = finding.quote + " -> " + replacement
    except Exception as e:
        pseudonymization_error = BackendError(
            status = "500",
            msg = "Fehler bei der Pseudonymisierung der Daten.",
            code = "DLP_ERROR"
        )
        logger.info(f"Error occurred during pseudonymization process: {e}")
        return None, None, pseudonymization_error
    return prompt, replacement_mapping, None

def anonymize_text(doc_content: str, project_id: str) -> tuple[str, str, BackendError]:
    """Anonymizes the given text and returns the anonymized text.

    This method anonymizes the provided text using the Google Cloud DLP API. It handles
    texts larger than the maximum allowed size by splitting them into smaller sections
    and processing each section individually.

    Args:
        doc_content: The text to be anonymized.
        project_id: The project ID of the Google Cloud project.

    Returns:
        A tuple containing:
            - The anonymized text.
            - An information message about the anonymization process.
            - A BackendError object if an error occurred, otherwise None.
    """
    if len(doc_content) > constants.MAX_PROMPT_SIZE_DLP:
        sections = _split_prompt(prompt=doc_content)
        anonymized_sections_list = []
        for section in sections:
            section_modified = section.replace("|", " ")
            dlp_resp = _call_dlp_api(prompt=section_modified, project_id=project_id)
            dlp_info = ""

            if len(dlp_resp.result.findings) == 0:
                continue
            if dlp_resp.result.findings_truncated:
                dlp_error = BackendError(
                    code="500",
                    msg=constants.DLP_TRUNCATED_FINDINGS,
                    status="DLP_ERROR"
                )
                return "", dlp_info, dlp_error

            anonymized_sections_list.append(_anonymize_text_section(text=section, findings=dlp_resp.result.findings))

        if len(anonymized_sections_list) == 0:
            return doc_content, dlp_info, None
        else:
            anonymized_text = " ".join(anonymized_sections_list)
            dlp_info = constants.DLP_INFO_ANONYMIZED
            logger.info(anonymized_text)
            return anonymized_text, dlp_info, None
    else:
        doc_content_modified = doc_content.replace("|", " ")
        dlp_resp = _call_dlp_api(prompt=doc_content_modified, project_id=project_id)
        dlp_info = ""

        if len(dlp_resp.result.findings) == 0:
            return doc_content, dlp_info, None

        if dlp_resp.result.findings_truncated:
            dlp_error = BackendError(
                code="500",
                msg=constants.DLP_TRUNCATED_FINDINGS,
                status="DLP_ERROR"
            )
            return "", dlp_info, dlp_error

        anonymized_text = _anonymize_text_section(text=doc_content, findings=dlp_resp.result.findings)

        dlp_info = constants.DLP_INFO_ANONYMIZED
        logger.info(anonymized_text)
        return anonymized_text, dlp_info, None


def inspect_prompt(
    prompt: str,
    project_id: str
    ) -> str:
    logger.info("Inspecting prompt %s", prompt)

    response = _call_dlp_api(prompt=prompt, project_id=project_id)

    num_findings = len(response.result.findings)
    findings_formatted = ""
    if num_findings > 0:
        findings_formatted = format_findings(response.result.findings)
    return {"num_findings": num_findings, "findings_formatted": findings_formatted}


def format_findings(findings: Sequence[Finding]) -> str:
    new_findings_format = "\n".join(
        [f"""{constants.DLP_INFO_TYPES_MAPPING[f.info_type.name]} : {f.quote}""" for f in findings],
    )

    return (
        f"Anscheinend beinhaltet die Frage persönliche Daten: \n\n"
        f"{new_findings_format}\n\n"
        "Deshalb kann ich die Frage nicht an die AI weiterleiten!"
    )
