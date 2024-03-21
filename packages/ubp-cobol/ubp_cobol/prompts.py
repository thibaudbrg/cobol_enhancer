# prompt_templates.py
from typing import Dict, Any

from ubp_cobol.utils import get_previous_critic_description


def process_file_next_prompt() -> str:
    """
    Constructs the dynamic prompt for processing the next COBOL file.
    """
    prompt_template = """
    You are a highly precise and proficient AI with expertise in programming and code optimization, specifically with COBOL code. Your task is to scrutinize the provided COBOL code, aiming to refactor it into the most efficient and error-free version possible. Focus on eliminating redundancy, optimizing the logic flow, correcting any errors, bad practices found or old practices (e.g. replace GO TO for PERFORM). It is crucial that the improvements maintain or enhance the original functionality of the code. 
    - Don't remove CONFIGURATION_SECTION,
    - Don't remove existing comments,
    - If you feel it necessary, add comments,
    - The existing comments should not be removed,

    It's crucial to preserve the original line numbers on the left side of each line of code. These line numbers are essential for tracking and documentation purposes. Please make sure that any modifications you suggest do not remove or alter these line numbers.

    It's crucial that you don't remove existing comments. Even more important, it is crucial that you add more comments for a better understanding.

    Please return only the improved COBOL code, with no additional comments or explanations. It's crucial to wrap the code into the markdown notation ```cobol [the_code] ```

    Here are the useful infos (metadatas) of the provided file:
    {metadata}



    And here is the COBOL file named {filename}:

    {old_code}
    """

    return prompt_template


def extender_prompt(state: Dict[str, Any]) -> str:
    """
    Builds a dynamic prompt for generating new versions of the code based on feedback.
    """

    template = (
        "You are an AI with expertise in COBOL, tasked with continuing the refinement of {filename}, a piece of code that has not been fully optimized or corrected. "
        "Your objective is to extend the existing enhancement, focusing on the parts of the code that have not been addressed yet. "
        "Ensure the continuation of the code remains true to its original functionality and improves upon it where possible.\n\n"
        "Based on the critics, continue to refine the code to solve any outstanding issues. "
        "Ensure your continuation is optimized, error-free, and faithful to the original's functionality. "
        "Output only the new, non-already generated portion of the code.\n\n"
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
            "Original Code:\n{old_code}\n\n"
            "Generated Code with errors:\n{new_code}\n\n"
        )
    else:
        # General enhancement template without specific demands or errors
        template_extension = (
            "Enhance the following COBOL code by refining and optimizing it while maintaining "
            "the original functionality. Ensure the final version is error-free:\n\n"
            "The critics:\n{critic}\n\n"
            "Original Code:\n{old_code}\n\n"
            "Generated but non finished Code:\n{new_code}\n\n"
        )

    return template + template_extension


def critic_generation_prompt(state: Dict[str, Any]) -> str:
    """
    Builds a dynamic prompt template for the critic generation phase based on the current state.
    """
    base_prompt = (
        "You are an expert in code analysis with a focus on COBOL. Examine the original code, "
        "the version before the latest changes (previous iteration code), and the new version. "
        "Identify any errors or discrepancies introduced in the new version. Provide a detailed critique, "
        "highlighting each issue with a thorough explanation and recommended solutions. Your review will guide "
        "developers"
        "in refining the code.\n\n"
    )

    prompt_sections = [
        "===========================================\n",
        f"Original COBOL Code:\n{state.get('old_code', '')}\n\n",
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

    previous_critic_description = get_previous_critic_description(state)
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

    return base_prompt + "".join(prompt_sections)


def new_generation_prompt(state: Dict[str, Any]) -> str:
    """
    Builds a dynamic prompt for generating new versions of the code based on feedback.
    """
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
            "Original Code:\n{old_code}\n\n"
            "Generated Code with errors:\n{new_code}\n\n"
        )
    else:
        # General enhancement template without specific demands or errors
        template_extension = (
            "Enhance the following COBOL code by refining and optimizing it while maintaining "
            "the original functionality. Ensure the final version is error-free:\n\n"
            "The critics:\n{critic}\n\n"
            "Original Code:\n{old_code}\n\n"
            "Generated Code:\n{new_code}\n\n"
        )

    return template + template_extension
