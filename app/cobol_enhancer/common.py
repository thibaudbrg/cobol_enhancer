from typing import List, Dict, TypedDict

from google.ai.generativelanguage_v1 import HarmCategory
from google.generativeai.types import HarmBlockThreshold


# Define a custom exception for exiting the workflow
class WorkflowExit(Exception):
    pass


class GraphState(TypedDict):
    files_to_process: List[str]
    filename: str
    original_critic: Dict[str, str]
    critic: Dict[str, str]
    old_code: str
    previous_last_gen_code: str
    new_code: str
    specific_demands: str
    copybooks: Dict[str, str]
    atlas_answer: str
    atlas_message_type: str
    human_decision: str


MODEL_NAME = "gpt-4-turbo-preview"
# MODEL_NAME = "gpt-3.5-turbo"
GEMINI = "models/gemini-1.5-pro-latest"
GEMINI_SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}
