from typing import List, Dict, TypedDict

class FileMetadata(TypedDict):
    dependencies: List[str]

class GraphState(TypedDict):
    files_to_process: List[str]
    file_metadata: Dict[str, FileMetadata]
    metadata: FileMetadata
    filename: str
    critic: Dict[str, str]
    old_code: str
    previous_last_gen_code: str
    new_code: str
    specific_demands: str
    copybooks: Dict[str, str]

MODEL_NAME = "gpt-4-turbo-preview"
#MODEL_NAME = "gpt-3.5-turbo"