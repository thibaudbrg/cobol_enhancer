from typing import List, Dict, TypedDict, Any
import os
from langchain import hub
from langgraph.graph import END, StateGraph
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langchain_core.output_parsers import StrOutputParser
from langchain.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.utils.function_calling import convert_to_openai_tool
from termcolor import colored
import shutil, difflib


MODEL_NAME = "gpt-4-turbo-preview"


# Utility functions for UI
def print_heading(heading: str):
    print(colored(f"\n{heading}\n", 'cyan', attrs=['bold']))

def print_subheading(subheading: str):
    print(colored(f"{subheading}", 'yellow'))

def print_info(info: str):
    print(colored(f"{info}", 'green'))

def print_error(error: str):
    print(colored(f"{error}", 'red'))

def _sanitize_output(text: str):
    possible_delimiters = ["```cobol", "```plaintext"]
    for delimiter in possible_delimiters:
        if delimiter in text:
            _, after = text.split(delimiter)
            code = after.split("```")[0]
            return code.strip()
    return text.strip()

class FileMetadata(TypedDict):
    dependencies: List[str]

class GraphState(TypedDict):
    files_to_process: List[str]
    file_metadata: Dict[str, FileMetadata]
    critic: Dict[str, str]
    previous_last_gen_code: str
    new_code: str
    specific_demands: str

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
    updated_state["new_code"] = _sanitize_output(result)
    print_info(f"Processed file: {current_file}")
    return updated_state

def critic_gen(state: GraphState):
    print_heading("CRITIC GENERATION")
    current_file = state["files_to_process"][0]
    with open(current_file, 'r') as file:
        old_code = file.read()
    new_code = state["new_code"]
    
    # Ensure 'critic' exists in state and is not None, and it has at least one element
    if state.get("critic") and len(state["critic"]) > 0 and hasattr(state["critic"][0], 'description'):
        previous_critic = state["critic"][0].description
        previous_last_gen_code = state["previous_last_gen_code"]
    else:
        previous_critic = ""
        previous_last_gen_code = ""

    prompt = hub.pull("thibaudbrg/cobol-code-comp")
    model = ChatOpenAI(temperature=0, model=MODEL_NAME, streaming=True)

    class CodeReviewResult(BaseModel):
        description: str = Field(description="The written critique of the code comparison.")
        grade: str = Field(description="Binary score 'good' or 'bad'.")

    review_tool_oai = convert_to_openai_tool(CodeReviewResult)
    llm_with_tool = model.bind(
        tools=[review_tool_oai],
        tool_choice={"type": "function", "function": {"name": "CodeReviewResult", "args": {"description": "description", "grade": "grade"}}},
    )
    parser_tool = PydanticToolsParser(tools=[CodeReviewResult])

    chain = prompt | llm_with_tool | parser_tool

    result = chain.invoke({"old_code": old_code,
                           "specific_demands": state["specific_demands"],
                           "previous_critic": previous_critic,
                           "previous_last_gen_code": previous_last_gen_code,
                           "new_code": new_code})

    updated_state = state.copy()
    updated_state["critic"] = result

    print_info(f"description: {updated_state['critic'][0].description}")
    print_info(f"grade: {updated_state['critic'][0].grade}")
    return updated_state

def eval_decider(state: GraphState):
    print_heading("EVALUATION DECIDER")
    grade = state["critic"][0].grade

    if grade == "good":
        human_input = human_review(state)  # Incorporate human review with enhanced UI

        if "specific_demands" in state and state["specific_demands"]:
            print_info(f"Regenerating based on specific demands: {state['specific_demands']}")
            return "re_gen"
        else:
            current_file = state["files_to_process"].pop(0)
            output_file_path = current_file.replace("data/input/", "data/output/")
            justification_file_path = output_file_path.replace('.cob', '_justification.md')

            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

            with open(output_file_path, 'w') as file:
                file.write(state["new_code"])
            print_info(f"Saved improved code to: {output_file_path}")

            with open(justification_file_path, 'w') as jfile:
                jfile.write(state["critic"][0].description)
            print_info(f"Saved justification to: {justification_file_path}")

            # Clear state for the next iteration or conclusion
            state["previous_last_gen_code"] = ""
            state["new_code"] = ""
            state["critic"] = []

            if not state["files_to_process"]:
                print_info("All files have been processed.")
                return "end"
            else:
                return "start_next_file_process"
    else:
        print_error("Critic has identified issues. Initiating regeneration...")
        return "re_gen"
    
def print_diff_line(line, width, prefix_length=2):
    # Adjust the line width for the prefix
    line_content = line[prefix_length:].rstrip()
    return f"{line_content:<{width - prefix_length}}"

def human_review(state: GraphState) -> GraphState:
    print_heading("HUMAN REVIEW")

    # Get terminal width and calculate half for side-by-side view
    terminal_width = shutil.get_terminal_size().columns
    half_terminal_width = terminal_width // 2

    current_file = state["files_to_process"][0]
    with open(current_file, 'r') as file:
        old_code = file.read()

    # Split the code into lines for diffing
    old_code_lines = old_code.split('\n')
    new_code_lines = state["new_code"].split('\n')

    # Use difflib to get the diff
    diff = list(difflib.ndiff(old_code_lines, new_code_lines))

    print_subheading("Side-by-side comparison (Old vs. New):")
    print("=" * terminal_width)

    # Process the diff output
    for line in diff:
        if line.startswith("- "):
            print(colored(print_diff_line(line, half_terminal_width), 'red'), end="")
        elif line.startswith("+ "):
            print(colored(print_diff_line(line, half_terminal_width), 'green'), end="")
        elif line.startswith("? "):
            # Skip the detail lines from difflib output
            continue
        else:
            print(print_diff_line(line, half_terminal_width), end="")

        print(' |', end="")  # Separator for the columns

        if line.startswith("- "):
            # For removed lines, we'll leave the new code column empty
            print(" " * (half_terminal_width - 1))
        elif line.startswith("+ "):
            # For added lines, we'll print again on the right
            print(colored(print_diff_line(line, half_terminal_width), 'green'))
        else:
            # For unchanged lines, print the line again in the new code column
            print(print_diff_line(line, half_terminal_width))

    print("=" * terminal_width)

    while True:
        human_decision = input("Accept changes? (yes/no): ").strip().lower()
        if human_decision == "yes":
            print_info("Changes accepted. Moving to the next file.")
            state["specific_demands"] = ""
            break
        elif human_decision == "no":
            print_error("Changes not accepted. Please provide specific demands for regeneration:")
            specific_demands = input("Enter demands: ").strip()
            state["specific_demands"] = specific_demands
            break
        else:
            print_error("Error: Please enter 'yes' or 'no'.")

    return state

def new_gen(state: GraphState) -> GraphState:
    print_heading("NEW GENERATION BASED ON FEEDBACK")
    prompt = hub.pull("thibaudbrg/cobol-new-gen")
    model = ChatOpenAI(temperature=0, model=MODEL_NAME, streaming=True)

    chain = prompt | model | StrOutputParser()

    with open(state["files_to_process"][0], 'r') as file:
        old_code = file.read()
    
    result = chain.invoke({
        "metadata": state["file_metadata"],
        "filename": os.path.basename(state["files_to_process"][0]),
        "critic": state["critic"][0].description,
        "specific_demands": state["specific_demands"],
        "old_code": old_code,
        "new_code": state["new_code"]
    })
    
    updated_state = state.copy()
    updated_state["specific_demands"] = ""
    updated_state["previous_last_gen_code"] = state["new_code"]
    updated_state["new_code"] = _sanitize_output(result)
    return updated_state

workflow = StateGraph(GraphState)

workflow.add_node("process_directory", process_directory)
workflow.add_node("process_file", process_file)
workflow.add_node("critic_gen", critic_gen)
workflow.add_node("new_gen", new_gen)

workflow.set_entry_point("process_directory")
workflow.add_edge("process_directory", "process_file")
workflow.add_edge("process_file", "critic_gen")
workflow.add_conditional_edges("critic_gen", eval_decider, {
    "re_gen": "new_gen",  # bad quality
    "start_next_file_process": "process_file",  # good quality
    "end": END # all files processed
})
workflow.add_edge("new_gen", "critic_gen")

app = workflow.compile()
