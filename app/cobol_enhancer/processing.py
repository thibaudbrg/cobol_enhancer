# Hacky trick to resolve an issue with pyreadline on Windows
# Manually patch the Callable in collections if it's not present
import collections.abc
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .common import GraphState, MODEL_NAME, WorkflowExit
from .prompts import process_file_next_prompt, analyze_file_prompt
from .utils import print_heading, print_info, print_error, extract_copybooks, \
    format_copybooks_for_display, filename_tab_completion, generate_code_with_history

if not hasattr(collections, 'Callable'):
    collections.Callable = collections.abc.Callable

try:
    # Attempt to import readline for Unix/Linux systems
    import readline
except ImportError:
    # Fallback for Windows, requiring pyreadline
    try:
        import pyreadline as readline
    except ImportError:
        print("pyreadline is required on Windows. Please install with 'pip install pyreadline'.")
        raise WorkflowExit


def process_directory(state: GraphState) -> GraphState:
    print_heading("PROCESSING DIRECTORY")

    # Set up tab completion for file names
    readline.set_completer(filename_tab_completion)
    readline.parse_and_bind("tab: complete")

    files_to_process = []

    while True:

        # Ask the user how they want to proceed: all files or a specific list
        choice = input(
            "Process all COBOL files in the directory (a), a specific list (s), or exit (e)? [a/s/e]: ").strip().lower()

        if choice == 'a':
            for root, dirs, files in os.walk("data/input/"):
                for file in files:
                    if file.endswith(".cob"):
                        file_path = os.path.join(root, file)
                        files_to_process.append(file_path)
            break
        elif choice == 's':
            print("Enter the filenames to process, separated by commas (Tab for autocompletion): ")
            specified_files = input().strip().split(',')
            for file in specified_files:
                file = file.strip()  # Remove any leading/trailing whitespace
                if file.endswith(".cob"):
                    file_path = os.path.join("data/input/", file)  # Assuming files are in 'data/input/'
                    if os.path.exists(file_path):
                        files_to_process.append(file_path)
                    else:
                        print_info(f"File not found: {file_path}")
                else:
                    print_info(f"Ignored non-COBOL file: {file}")
            break
        elif choice == 'e':  # Allow the user to exit the program
            print_info("Exiting program as requested.")
            raise WorkflowExit
        else:
            print_error(
                "Invalid choice. Please enter 'a' to process all files, 's' for a specific list, or 'e' to exit.")

    state["files_to_process"] = files_to_process

    if not files_to_process:
        print_info("No COBOL files to process. Exiting the program.")
        raise WorkflowExit  # Exit if no files are to be processed

    print_info(f"Files to process: {files_to_process}")
    return state


def analyze_file(state: GraphState) -> GraphState:
    print_heading("ANALYZING FILE")
    if not state["files_to_process"]:
        print_info("No more files to process.")
        return state

    current_file = state["files_to_process"][0]
    with open(current_file, 'r') as file:
        old_code = file.read()

    state["filename"] = os.path.basename(current_file)
    state["old_code"] = old_code
    state["copybooks"] = extract_copybooks(old_code)

    template = analyze_file_prompt()
    model = ChatOpenAI(temperature=0, model=MODEL_NAME, streaming=True)

    class CodeReviewResult(BaseModel):
        description: str = Field(description="The written critique of the code comparison.")
        grade: str = Field(description="Binary score 'good' or 'bad'.")

    chain = ChatPromptTemplate.from_template(template) | model.with_structured_output(CodeReviewResult)

    critic_response = chain.invoke({
        "filename": state["filename"],
        "old_code": state["old_code"],
        "copybooks": format_copybooks_for_display(state["copybooks"])
    })

    state["original_critic"] = critic_response.dict()

    print_info(f"Original Code Critic Description: {state['original_critic']['description']}")
    print_info(f"Critic Grade: {state['original_critic']['grade']}")
    return state


def process_next_file(state: GraphState) -> GraphState:
    print_heading("PROCESSING FILE")

    template = process_file_next_prompt()
    model = ChatOpenAI(temperature=0, model=MODEL_NAME, streaming=True)
    variables = {
        "filename": state["filename"],
        "old_code": state["old_code"],
        "copybooks": format_copybooks_for_display(state["copybooks"]),
        "original_critic": state["original_critic"]
    }

    state["new_code"] = generate_code_with_history(state, "process_next_file", template, model, variables)

    print_info(f"Processed file: {state['filename']}")

    return state
