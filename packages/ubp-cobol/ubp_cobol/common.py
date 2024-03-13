from typing import List, Dict, TypedDict

class FileMetadata(TypedDict):
    dependencies: List[str]

class GraphState(TypedDict):
    files_to_process: List[str]
    file_metadata: Dict[str, FileMetadata]
    critic: Dict[str, str]
    previous_last_gen_code: str
    new_code: str
    specific_demands: str

MODEL_NAME = "gpt-4-turbo-preview"