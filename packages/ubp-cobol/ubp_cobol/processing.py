import os
import json

from .common import GraphState, MODEL_NAME
from .utils import print_heading, print_info, sanitize_output, extract_copybooks, format_copybooks_for_display

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

    state["files_to_process"] = files_to_process
    state["file_metadata"] = file_metadata

    print_info(f"Files to process: {files_to_process}")
    return state


def process_file(state: GraphState) -> GraphState:
    print_heading("PROCESSING FILE")
    if not state["files_to_process"]:
        print_info("No more files to process.")
        return state

    current_file = state["files_to_process"][0]
    with open(current_file, 'r') as file:
        old_code = file.read()

    state["metadata"] = state["file_metadata"][current_file]
    state["filename"] = os.path.basename(current_file)
    state["old_code"] = old_code
    state["copybooks"] = extract_copybooks(old_code)

    prompt = hub.pull("thibaudbrg/cobol-code-gen")
    model = ChatOpenAI(temperature=0, model=MODEL_NAME, streaming=True)
    chain = prompt | model | StrOutputParser()
    result = chain.invoke(
        {"metadata": state["metadata"],
         "filename": state["filename"],
         "old_code": state["old_code"],
         "copybooks": format_copybooks_for_display(state["copybooks"])})

    state["new_code"] = result
    print_info(f"Processed file: {current_file}")

    return state


def finished(state: GraphState) -> str:
    print_heading("FINISHED DECIDER")
    result = state["new_code"]
    code_block_delimiter = "```"
    if not result.strip().endswith(code_block_delimiter):
        return "not_finished"
    else:
        state["new_code"] = sanitize_output(result)
        return "finished"


def extender(state: GraphState) -> GraphState:
    print_heading("EXTENDER")

    prompt = hub.pull("thibaudbrg/cobol-code-extender")
    model = ChatOpenAI(temperature=0, model=MODEL_NAME, streaming=True)

    chain = prompt | model | StrOutputParser()
    result = chain.invoke({"metadata": state["metadata"],
                           "filename": state["filename"],
                           "old_code": state["old_code"],
                           "not_finished_file": state["new_code"],
                           })

    state["new_code"] = state["new_code"] + "\n" + sanitize_output(result, True, False)
    return state
