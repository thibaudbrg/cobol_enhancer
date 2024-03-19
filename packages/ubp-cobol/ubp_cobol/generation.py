from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .common import MODEL_NAME, GraphState
from .utils import print_heading, print_info, print_error, sanitize_output, \
    format_copybooks_for_display, print_code_comparator


def critic_gen(state: GraphState) -> GraphState:
    print_heading("CRITIC GENERATION")

    # Ensure 'critic' exists in state, is a dictionary, and has a 'description' key
    if "critic" in state and isinstance(state["critic"], dict) and "description" in state["critic"]:
        previous_critic_description = state["critic"]["description"]
    else:
        previous_critic_description = ""

    # Building the dynamic prompt with more descriptive context
    base_prompt = (
        "You are an expert in code analysis with a focus on COBOL. Examine the original code, "
        "the version before the latest changes (previous iteration code), and the new version. "
        "Identify any errors or discrepancies introduced in the new version. Provide a detailed critique, "
        "highlighting each issue with a thorough explanation and recommended solutions. Your review will guide developers "
        "in refining the code.\n\n"
    )

    # Append to the prompt with descriptive contexts based on the state
    prompt_sections = [
        "===========================================\n",
        "Original COBOL Code:\n{old_code}\n\n",
    ]

    if "previous_iteration_code" in state and state["previous_last_gen_code"]:
        prompt_sections.append(
            "Previously Iterated COBOL Code (T-1 Version):\nThis code reflects the state prior to the most "
            "recent changes and serves as a benchmark against the new version.\n"
            "{previous_iteration_code}\n\n"
        )

    if "specific_demands" in state and state["specific_demands"]:
        prompt_sections.append(
            "Developer's Specific Critique:\nFeedback provided by the developer to address certain "
            "areas in the code that require special attention.\n"
            "{specific_demands}\n\n"
        )

    if previous_critic_description:
        prompt_sections.append(
            "Previous Critique Round:\nA look back at the last set of comments and whether the subsequent "
            "code adjustments have appropriately addressed those concerns.\n"
            "{previous_critic_description}\n\n"
        )

    if "atlas_answer" in state and state["atlas_answer"]:
        prompt_sections.append(
            "Atlas Error Trace:\nThe following errors were encountered during execution, which the new "
            "version of the code aims to resolve.\n"
            "{atlas_answer}\n\n"
        )

    prompt_sections.append(
        "Newly Generated COBOL Code for Review:\nThe latest version of the code, updated to rectify previous issues "
        "and optimize performance. This version is under scrutiny for accuracy and adherence to best practices.\n"
        "{new_code}\n"
    )

    # Concatenate the base prompt with the detailed sections
    full_prompt = base_prompt + "".join(prompt_sections)

    # Setup the model and the structured output parser
    model = ChatOpenAI(temperature=0, model=MODEL_NAME, streaming=True)

    # Define the Pydantic model for structured output
    class CodeReviewResult(BaseModel):
        description: str = Field(description="The written critique of the code comparison.")
        grade: str = Field(description="Binary score 'good' or 'bad'.")

    # Use the full prompt to call the model with structured output
    chain = ChatPromptTemplate.from_template(full_prompt) | model.with_structured_output(CodeReviewResult)


    # Invoke the chain with the filled-out prompt
    try:
        critic_response = chain.invoke({
            "old_code": state["old_code"],
            "previous_iteration_code": state.get("previous_last_gen_code", ""),
            "specific_demands": state.get("specific_demands", ""),
            "previous_critic": previous_critic_description,
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


def eval_decider(state: GraphState):
    print_heading("EVALUATION DECIDER")
    grade = state["critic"]["grade"]

    if grade == "good":
        human_review(state)  # Incorporate human review with enhanced UI

        if "specific_demands" in state and state["specific_demands"]:
            print_info(f"Regenerating based on specific demands: {state['specific_demands']}")
            return "re_gen"
        else:
            # Print the file ready to be sent message
            print_info(f"The file {state['filename']} can be sent.")
            return "send_file"  # Indicate the file is ready to be sent
    else:
        print_error("Critic has identified issues. Initiating regeneration...")
        return "re_gen"


def print_diff_line(line, width, prefix_length=2):
    # Adjust the line width for the prefix
    line_content = line[prefix_length:].rstrip()
    return f"{line_content:<{width - prefix_length}}"


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
        elif human_decision == "no" and not specific_demands_provided:
            print_error("Changes not accepted. Please provide specific demands for regeneration:")
            specific_demands = input("Enter demands: ").strip()
            state["specific_demands"] = specific_demands
            specific_demands_provided = True

            # Ask if they want to reconsider their decision
            reconsider = input("Would you like to reconsider accepting the changes? (yes/no): ").strip().lower()
            if reconsider == "yes":
                decision_made = True  # They've reconsidered; exit loop
            elif reconsider == "no":
                print_info("Understood. Keeping the original decision to reject the changes.")
                decision_made = True  # Confirming their decision to reject; exit loop
            else:
                print_error("Error: Please enter 'yes' or 'no'.")
        else:
            print_error("Error: Please enter 'yes' or 'no'.")

    return state


def new_gen(state: GraphState) -> GraphState:
    print_heading("NEW GENERATION BASED ON FEEDBACK")

    # Initialize base prompt
    template = (
        "You are an AI with expertise in COBOL, tasked with refining a piece of code. "
        "A new version of {filename} has been generated to improve upon the old code. "
        "Your objective is to correct these mistakes, ensuring the updated code remains "
        "true to its original functionality and improves upon it where possible.\n\n"
        "Based on the critics and utilizing the metadata, refine the generated code to solve the identified issues. "
        "Ensure the final version is optimized, error-free, and faithful to the original's functionality. "
        "Your output should be the corrected code only.\n\n"
        "It's crucial that you don't remove existing comments. Even more important, it is crucial that you add more comments for a better understanding.\n\n"
        "It's crucial to preserve the original line numbers on the left side of each line of code. "
        "These line numbers are essential for tracking and documentation purposes. Please make sure that any modifications you suggest do not remove or alter these line numbers.\n\n"
    )

    # Customize the prompt based on the case
    if "atlas_message_type" in state and state["atlas_message_type"]:
        # For compilation or execution errors
        template_extension = (
            "The COBOL code has encountered a {atlas_message_type}. Correct the code "
            "to address the following issue and ensure it is optimized and error-free:\n\n"
            "{atlas_answer}\n\n"
            "Original Code:\n{old_code}\n\n"
            "Generated Code with errors:\n{new_code}\n\n"
        )
    elif "specific_demands" in state and state["specific_demands"]:
        # For feedback with specific demands
        template_extension = (
            "Refine the COBOL code according to the specific demands of the developer "
            "and ensure that all improvements are faithful to the original functionality:\n\n"
            "{specific_demands}\n\n"
            "Metadata: {metadata}\n"
            "Copybooks: {copybooks}\n\n"
            "Original Code:\n{old_code}\n\n"
            "Generated Code with errors:\n{new_code}\n\n"
        )
    else:
        # General enhancement template without specific demands or errors
        template_extension = (
            "Enhance the following COBOL code by refining and optimizing it while maintaining "
            "the original functionality. Ensure the final version is error-free:\n\n"
            "Metadata: {metadata}\n"
            "Copybooks: {copybooks}\n\n"
            "Original Code:\n{old_code}\n\n"
            "Generated Code:\n{new_code}\n\n"
        )

    prompt = ChatPromptTemplate.from_template(template + template_extension)
    model = ChatOpenAI(temperature=0, model=MODEL_NAME, streaming=True)

    chain = prompt | model | StrOutputParser()

    # Invoke the OpenAI model with the formatted prompt
    result = chain.invoke({
        "filename": state["filename"],
        "critic": state.get("critic", {}).get("description", ""),
        "specific_demands": state.get("specific_demands", ""),
        "metadata": state["metadata"],
        "copybooks": format_copybooks_for_display(state["copybooks"]),
        "old_code": state["old_code"],
        "new_code": state["new_code"],
        "atlas_answer": state.get("atlas_answer", ""),
        "atlas_message_type": state.get("atlas_message_type", "").replace('_', ' ').capitalize()
    })

    state["previous_last_gen_code"] = state.get("new_code", "")
    state["new_code"] = sanitize_output(result)

    # Reset atlas-related state information if it was used during this execution
    if "atlas_message_type" in state and state["atlas_message_type"]:
        state["atlas_answer"] = ""
        state["atlas_message_type"] = ""

    return state
