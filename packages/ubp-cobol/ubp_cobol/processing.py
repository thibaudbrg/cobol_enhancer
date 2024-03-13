import os
from typing import List, TypedDict

from .common import GraphState, MODEL_NAME
from .utils import print_heading, print_info, sanitize_output

from langchain import hub
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser


def process_directory(state: GraphState) -> GraphState:
    print_heading("PROCESSING DIRECTORY")
    files_to_process = []
    file_metadata = {}

    for root, dirs, files in os.walk("data/input/"):
        for file in files:
            if file.endswith(".cob"):
                file_path = os.path.join(root, file)
                files_to_process.append(file_path)
                file_metadata[file_path] = {"dependencies": [], "other_info": {}}

    updated_state = state.copy()
    updated_state["files_to_process"] = files_to_process
    updated_state["file_metadata"] = file_metadata

    print_info(f"Files to process: {files_to_process}")
    return updated_state

def process_file(state: GraphState) -> GraphState:
    print_heading("PROCESSING FILE")
    if not state["files_to_process"]:
        print_info("No more files to process.")
        return state

    current_file = state["files_to_process"][0]
    metadata = state["file_metadata"][current_file]

    with open(current_file, 'r') as file:
        file_content = file.read()

    prompt = hub.pull("thibaudbrg/cobol-code-gen")
    model = ChatOpenAI(temperature=0, model=MODEL_NAME, streaming=True)

    chain = prompt | model | StrOutputParser()
    result = chain.invoke({"metadata": metadata, "filename": os.path.basename(current_file), "file": file_content})

    updated_state = state.copy()
    updated_state["new_code"] = sanitize_output(result)
    print_info(f"Processed file: {current_file}")
    return updated_state