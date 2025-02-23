"""Application constants."""

########################
## LLM Model Settings ##
########################

IMAGEN_DEFAULT_MODEL_NAME = "imagen-3.0-generate-001"
IMAGEN_NUM_IMAGES = 3

GEMINI_TEXT_CHAT_DEFAULT_MODEL_NAME = "gemini-1.5-pro-002"
GEMINI_TEXT_CHAT_DEFAULT_TEMPERATURE = 1.0
GEMINI_MAX_OUTPUT_TOKENS = 2048

TEXT_CHAT_DEFAULT_MODEL_NAME = "chat-bison-32k"
TEXT_CHAT_DEFAULT_TEMPERATURE = 0.2
MAX_OUTPUT_TOKENS = 256

CODE_CHAT_MAX_OUTPUT_TOKENS:int = 2048


SYSTEM_INSTRUCTION_GEMINI_TEXT_CHAT=[
    "You are a helpful Chat Assistant for Employees of Signal Iduna.",
    "You respond to their questions truthfully and accurately."
    "You answer in german."
]

########################
####### DOC CHAT #######
########################


DOC_CHAT_PLACEHOLDER_MESSAGE = "Ich warte auf den User Prompt."

SYSTEM_INSTRUCTION_GEMINI_DOC_CHAT = [
    "You are a helpful Chat Assistant for Employees of Signal Iduna.",
    "You respond to their questions truthfully and accurately.",
    "You answer in german.",
    "If provided use the context to answer the questions. The context is provided inside the <KONTEXT> tag"
]

SYSTEM_INSTRUCTION_GEMINI_KATALOG = [
    """
    Du bist ein Chatbot-Assistent für die Signal Iduna und beantwortest Fragen
    über Strategiepapier der SIGNAL IDUNA Gruppe mit dem Titel "MOMENTUM 2030".
    Es beschreibt die Unternehmensstrategie für die kommenden Jahre bis 2030.
    Du hast Zugriff auf eine Zusammenfassung des Strategiepapiers im Abschnitt
    <ZUSAMMENFASSUNG>.
    Du hast Zugriff auf einem Fragenkatalog zum Strategieapier im Abschnitt
    <FRAGENKATALOG>.
    Falls du eine Frage im Fragenkatalog findest, dann beantworte sie mit
    den Informationen aus der Antwort aus dem Fragenkatalog.
    Du darfst die Antwort bearbeiten, formatieren und wichtige Punkte hervorheben.
    Bitte schreibe KEINE XML-Tags wie zum Beispiel <Frage3> in die Antwort.
    In deiner Antwort soll kein XML sein. Du darfst die Antwort auch kürzen
    und komprimieren.
    Wenn eine Frage nicht im Fragenkatalog zu oder der Zusammenfassung
    zu finden ist, antworte mit NOT_FOUND
    Deine Antwort soll nicht länger als 500 Wörter sein. Benutze maximal
    500 Output-Token für deine Antwort.
    """
]

SYSTEM_INSTRUCTION_GEMINI_STRATEGIE = [
    """
    Du bist ein Chatbot-Assistent für die Signal Iduna und beantwortest Fragen
    über Strategiepapier der SIGNAL IDUNA Gruppe mit dem Titel "MOMENTUM 2030".
    Es beschreibt die Unternehmensstrategie für die kommenden Jahre bis 2030.
    Du hast über den <KONTEXT> Zugriff auf das gesamte Strategie-Papier.
    """
]

SYSTEM_INSTRUCTION_TRANSLATION_IMAGEN = [
    "You are a translator that takes input in any language and translates this input to English.",
    "You must not change the content.",
    "You must translate precisely.",
    "If the input is already in English, do not translate it but simply return the original input."
]

DEFAULT_CONTEXT =  """
SYSTEM: You are a helpful Chat Assistant for Employees of Signal Iduna.
You respond to their questions truthfully and accurately.
Prefer using your general knowledge to answer the questions.
You may use the provided chat history if it contains relevant information.
ALWAYS USE YOUR GENERAL KNOWLEDGE FIRST TO ANSWER QUESTIONS.
IF YOU CANNOT ANSWER A QUESTION WITH THE CONTEXT THEN DON'T USE THE CONTEXT.
"""


VERTEXAI_PARAMS = {
    "temperature": 0.2,
    "max_output_tokens": 512,
    "top_p": 0.8,
    "top_k": 40,
}

CODE_CHAT_DEFAULT_MODEL_NAME = "codechat-bison-32k@002"


#################
## DLP Related ##
#################
DEFAULT_INFO_TYPES = ["STREET_ADDRESS", "FIRST_NAME", "LAST_NAME", "PHONE_NUMBER"]
DEFAULT_MIN_LIKELIHOOD = "LIKELY"
DEFAULT_MIN_LIKELIHOOD_DOCUMENT = "VERY_LIKELY"
DEFAULT_MAX_FINDINGS = 0  # no limit
MAX_PROMPT_SIZE_DLP = 400000 # Error message is triggered when content size exceeds 524288
DLP_INFO_ANONYMIZED = "Personenbezug wurde im Dokument automatisch anonymisiert."
DLP_TRUNCATED_FINDINGS = "Das Dokument beinhaltet zu viele sensible Daten und kann daher nicht verarbeitet werden."

DLP_LIKELIHOODS = [
    "LIKELIHOOD_UNSPECIFIED",
    "VERY_UNLIKELY",
    "UNLIKELY",
    "POSSIBLE",
    "LIKELY",
    "VERY_LIKELY",
]

DLP_LIKELIHOOD_MAPPING = {
    "LIKELIHOOD_UNSPECIFIED": "Unbekannt",
    "VERY_UNLIKELY": "Sehr unwahrscheinlich",
    "UNLIKELY": "Unwahrscheinlich",
    "POSSIBLE": "Möglicherweise",
    "LIKELY": "Wahrscheinlich",
    "VERY_LIKELY": "Sehr wahrscheinlich",
}

DLP_INFO_TYPES_MAPPING = {
    "STREET_ADDRESS": "Adresse",
    "FIRST_NAME": "Vorname",
    "LAST_NAME": "Nachname",
    "PHONE_NUMBER": "Telefonnummer",
}

####################
## Error Messages ##
####################
IMAGE_CHAT_EMPTY_LIST_ERROR = """
Es konnte leider kein Inhalt generiert werden.
Die Ursache dafür kann ein Richtlinienverstoß, wie z. B. Personenbezug oder das Generieren einer Person sein.
Bitte versuche eine andere Formulierung.
"""

QUOTA_EXCEEDED_ERROR = """
Das globale Limit für die maximale Anzahl an Anfragen an das Large Language Model wurde temporär überschritten. Bitte versuche es in einer Minute nochmal.
"""
