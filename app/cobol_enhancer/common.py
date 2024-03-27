from typing import List, Dict, TypedDict


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
