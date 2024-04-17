# Hacky trick to resolve an issue with pyreadline on Windows
# Manually patch the Callable in collections if it's not present
import collections.abc
import os

from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_google_genai import GoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from pydantic import BaseModel, Field

from .common import GraphState, WorkflowExit, GEMINI, GEMINI_SAFETY_SETTINGS
from .prompts import critic_generation_prompt, analyze_file_prompt, generation_prompt
from .utils import print_heading, print_info, print_error, format_copybooks_for_display, print_code_comparator, \
    get_previous_critic_description, generate_code_with_history, filename_tab_completion, extract_copybooks

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


def analyze_next_file(state: GraphState) -> GraphState:
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

    model = GoogleGenerativeAI(model=GEMINI, safety_settings=GEMINI_SAFETY_SETTINGS)


    class CodeReviewResult(BaseModel):
        description: str = Field(description="The written critique of the code comparison.")
        grade: str = Field(description="Binary score 'good' or 'bad'.")

    output_parser = PydanticOutputParser(pydantic_object=CodeReviewResult)
    prompt = PromptTemplate(
        template=analyze_file_prompt() + "\n{format_instructions}\n",
        input_variables=["filename", "old_code"],
        partial_variables={"format_instructions": output_parser.get_format_instructions()},
    )
    chain = prompt | model | output_parser

    critic_response = chain.invoke({
        "filename": state["filename"],
        "old_code": state["old_code"],
        "copybooks": format_copybooks_for_display(state["copybooks"])
    })

    state["original_critic"] = critic_response.dict()

    print_info(f"Original Code Critic Description: {state['original_critic']['description']}")
    print_info(f"Critic Grade: {state['original_critic']['grade']}")
    return state


def generate(state: GraphState) -> GraphState:
    print_heading("GENERATION")

    template = generation_prompt(state)
    model = GoogleGenerativeAI(model=GEMINI, safety_settings=GEMINI_SAFETY_SETTINGS)

    variables = {
        "filename": state["filename"],
        "copybooks": format_copybooks_for_display(state["copybooks"]),
        "old_code": state["old_code"],
        "original_critic": state["original_critic"],
        "new_code": state.get("new_code", ""),
        "critic": (state.get("critic") or {}).get("description", ""),
        "specific_demands": state.get("specific_demands", ""),
        "atlas_answer": state.get("atlas_answer", ""),
        "atlas_message_type": (state.get("atlas_message_type") or "").replace('_', ' ').capitalize()
    }

    # Does nothing if first generation
    state["previous_last_gen_code"] = state.get("new_code", "")

    # Reset atlas-related state information if it was used during this execution
    if "atlas_message_type" in state and state["atlas_message_type"]:
        state["atlas_answer"] = ""
        state["atlas_message_type"] = ""

    # state["new_code"] = generate_code_with_history(state, "process_next_file", template, model, variables)
    chain = ChatPromptTemplate.from_template(template) | model | StrOutputParser()

    # Use stream instead of invoke
    new_code_accumulated = ""
    for chunk in chain.stream({**variables}):
        print(chunk, end="", flush=True)
        new_code_accumulated += chunk

    # Save the accumulated output to the state
    state["new_code"] = new_code_accumulated

    # After first generation, clear the original_critic
    state["original_critic"] = {}

    print_info(f"Generated file: {state['filename']}")

    return state


def critic_generation(state: GraphState) -> GraphState:
    print_heading("CRITIC GENERATION")

    # Set up the model and the structured output parser
    model = GoogleGenerativeAI(model=GEMINI, safety_settings=GEMINI_SAFETY_SETTINGS)

    # Define the Pydantic model for structured output
    class CodeReviewResult(BaseModel):
        description: str = Field(description="The written critique of the code comparison.")
        grade: str = Field(description="Binary score 'good' or 'bad'.")

    output_parser = PydanticOutputParser(pydantic_object=CodeReviewResult)
    prompt = PromptTemplate(
        template=critic_generation_prompt(state) + "\n{format_instructions}\n",
        input_variables=["old_code", "previous_iteration_code", "specific_demands", "previous_critic_description", "atlas_answer", "new_code", "atlas_message_type"],
        partial_variables={"format_instructions": output_parser.get_format_instructions()},
    )

    # Use the full prompt to call the model with structured output
    chain = prompt | model | output_parser

    # Invoke the chain with the filled-out prompt
    try:
        critic_response = chain.invoke({
            "old_code": state["old_code"],
            "previous_iteration_code": state.get("previous_last_gen_code", ""),
            "specific_demands": state.get("specific_demands", ""),
            "previous_critic_description": get_previous_critic_description(state),
            "atlas_answer": state.get("atlas_answer", ""),
            "new_code": state["new_code"],
            "atlas_message_type": (state.get("atlas_message_type") or "").replace('_', ' ').capitalize()
        })

        # Update the state with the critic information
        state["critic"] = critic_response.dict()

        print_info(f"Critic Description: {state['critic']['description']}")
        print_info(f"Critic Grade: {state['critic']['grade']}")
    except Exception as e:
        print_error(f"Error during critic generation: {e}")
        # Provide default values in case of an error
        state["critic"] = {"description": "An error occurred during critique generation.", "grade": "bad"}

    return state


def human_review(state: GraphState) -> GraphState:
    print_heading("HUMAN REVIEW")

    print_code_comparator(state["old_code"], state["new_code"])

    decision_made = False
    specific_demands_provided = False

    while not decision_made:
        human_decision = input("Accept changes? (yes/no): ").strip().lower()
        if human_decision == "yes":
            print_info("Changes accepted. Moving to the next file.")
            state["specific_demands"] = ""
            decision_made = True
            state["human_decision"] = "yes"
        elif human_decision == "no" and not specific_demands_provided:
            print_error("Changes not accepted. Please provide specific demands for regeneration:")
            specific_demands = input("Enter demands: ").strip()
            state["specific_demands"] = specific_demands
            specific_demands_provided = True
            state["human_decision"] = "no"

            # Ask if they want to reconsider their decision
            reconsider = input("Would you like to reconsider accepting the changes? (yes/no): ").strip().lower()
            if reconsider == "yes":
                decision_made = True  # They've reconsidered; exit loop
                state["human_decision"] = "yes"
            elif reconsider == "no":
                print_info("Understood. Keeping the original decision to reject the changes.")
                decision_made = True  # Confirming their decision to reject; exit loop
                state["human_decision"] = "no"
            else:
                print_error("Error: Please enter 'yes' or 'no'.")
        else:
            print_error("Error: Please enter 'yes' or 'no'.")

    return state
