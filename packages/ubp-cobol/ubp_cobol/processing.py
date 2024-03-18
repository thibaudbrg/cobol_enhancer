import os
import sys

from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from .common import GraphState, MODEL_NAME
from .utils import print_heading, print_info, print_error, sanitize_output, extract_copybooks, \
    format_copybooks_for_display

try:
    # Attempt to import readline for Unix/Linux systems
    import readline
except ImportError:
    # Fallback for Windows, requiring pyreadline
    try:
        import pyreadline as readline
    except ImportError:
        print("pyreadline is required on Windows. Please install with 'pip install pyreadline'.")
        sys.exit(1)


def complete(text, state):
    # List all file names in data/input/, filtering by the current input text
    files = [f for f in os.listdir("data/input/") if f.startswith(text)]
    # Return the state-th file name if it exists, appending a space for convenience
    return (files[state] + " ") if state < len(files) else None


def process_directory(state: GraphState) -> GraphState:
    print_heading("PROCESSING DIRECTORY")

    # Set up tab completion for file names
    readline.set_completer(complete)
    readline.parse_and_bind("tab: complete")

    # Ask the user how they want to proceed: all files or a specific list
    choice = input("Process all COBOL files in the directory (a) or a specific list (s)? [a/s]: ").strip().lower()
    files_to_process = []
    file_metadata = {}

    if choice == 'a':
        for root, dirs, files in os.walk("data/input/"):
            for file in files:
                if file.endswith(".cob"):
                    file_path = os.path.join(root, file)
                    files_to_process.append(file_path)
                    file_metadata[file_path] = {"dependencies": [], "other_info": {}}
    elif choice == 's':
        print("Enter the filenames to process, separated by commas (Tab for autocompletion): ")
        specified_files = input().strip().split(',')
        for file in specified_files:
            file = file.strip()  # Remove any leading/trailing whitespace
            if file.endswith(".cob"):
                file_path = os.path.join("data/input/", file)  # Assuming files are in 'data/input/'
                if os.path.exists(file_path):
                    files_to_process.append(file_path)
                    file_metadata[file_path] = {"dependencies": [], "other_info": {}}
                else:
                    print_info(f"File not found: {file_path}")
            else:
                print_info(f"Ignored non-COBOL file: {file}")
    else:
        print_error("Invalid choice. Exiting.")
        sys.exit(1)

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
