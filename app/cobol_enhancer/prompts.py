from typing import Dict, Any

from app.cobol_enhancer.utils import get_previous_critic_description


def analyze_file_prompt() -> str:
    prompt = """
        You are an expert in code analysis with a focus on COBOL. Examine the original provided code: {filename}. 
        Identify any errors, discrepancies or possible enhancement with good usages. Provide a detailed critique, 
        highlighting each issue with a thorough explanation and recommended solutions. Your review will guide 
        developers in refining the code. This version is under scrutiny for accuracy and adherence to best 
        practices.

        Among all of your critics, it's crucial to focus on the following aspects:
        - Check for more comments for a better understanding, not too much tho, just the right amount.
        - Argue about the termination method. The termination method must not be changed.
        - Argue that the original line numbers on the left side of each line of code must be preserved. In fact some
        developers do sign here by replacing the 6 digit number, these line numbers are essential for
        tracking who wrote the lines purposes. So don't remove or alter these line numbers or pseudos if they are there.
        
        It's crucial that overall you don't try to announce changes everywhere, just subtle but meaningful changes.
        
        ===========================================
        Original COBOL Code:
        
        {old_code}
    """

    return prompt


def critic_generation_prompt(state: Dict[str, Any]) -> str:
    """
    Builds a dynamic prompt template for the critic generation phase based on the current state.
    """
    base_prompt = (
        "You are an expert in code analysis with a focus on COBOL. Examine the original code, "
        "the version before the latest changes (previous iteration code), and the new version. "
        "Identify any errors or discrepancies introduced in the new version. Provide a detailed critique, "
        "highlighting each issue with a thorough explanation and recommended solutions. Your review will guide "
        "developers in refining the code.\n\n"
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


def generation_prompt(state: Dict[str, Any]) -> str:
    if "original_critic" in state and state["original_critic"]:
        prompt_template = """
            You are an AI with expertise in COBOL, tasked with refining a piece of code. 
            Your objective is to correct these mistakes, ensuring the updated code remains 
            true to its original functionality and improves upon it where possible.

            Based on the critics, refine the code to solve the identified issues. 
            Ensure the final version is optimized, error-free, and faithful to the original's functionality. 
            Your output should be the corrected code only.

            It's crucial that you don't remove existing comments. Even more important, it is crucial that you add more 
            comments for a better understanding, not too much tho, just the right amount.

            It's crucial to NOT change the termination method of the program. For example, don't introduce a new termination
            method like "STOP RUN" if it was not there before.

            It's crucial to preserve the original line numbers on the left side of each line of code. Some developers do sign
            here by replacing the 6 digit number.
            These line numbers are essential for tracking and documentation purposes. Please make sure that any 
            modifications you suggest do not remove or alter these line numbers.
            """

        template_extension = """
        Enhance the following COBOL code by refining and optimizing it while maintaining 
        the original functionality. Ensure the final version is error-free:

        Original Code:
        {old_code}
        
        The critics:
        {original_critic}
        """
    else:
        prompt_template = """
            You are an AI with expertise in COBOL, tasked with refining a piece of code. 
            A new version of {filename} has been generated to improve upon the old code. 
            Your objective is to correct these mistakes, ensuring the updated code remains 
            true to its original functionality and improves upon it where possible.

            Based on the critics, refine the generated code to solve the identified issues. 
            Ensure the final version is optimized, error-free, and faithful to the original's functionality. 
            Your output should be the corrected code only.

            It's crucial that you don't remove existing comments. Even more important, it is crucial that you add more 
            comments for a better understanding, not too much tho, just the right amount.

            It's crucial to NOT change the termination method of the program. For example, don't introduce a new termination
            method like "STOP RUN" if it was not there before.

            It's crucial to preserve the original line numbers on the left side of each line of code. Some developers do sign
            here by replacing the 6 digit number.
            These line numbers are essential for tracking and documentation purposes. Please make sure that any 
            modifications you suggest do not remove or alter these line numbers.
            """

        if "atlas_message_type" in state and state["atlas_message_type"]:
            template_extension = """
            The COBOL code has encountered a {atlas_message_type}. Correct the code 
            to address the following issue and ensure it is optimized and error-free:
        
            {atlas_answer}
        
            Original Code:
            {old_code}
        
            Generated Code with errors:
            {new_code}
            """
        elif "specific_demands" in state and state["specific_demands"]:
            template_extension = """
            Refine the COBOL code according to the specific demands of the developer 
            and ensure that all improvements are faithful to the original functionality:
            
            Specific demands:
            {specific_demands}
        
            Original Code:
            {old_code}
        
            Generated Code with errors:
            {new_code}
            """
        else:
            template_extension = """
            Enhance the following COBOL code by refining and optimizing it while maintaining 
            the original functionality. Ensure the final version is error-free:
        
            The critics:
            {critic}
        
            Original Code:
            {old_code}
        
            Generated Code:
            {new_code}
            """

    return prompt_template + template_extension


def message_type_decider_prompt() -> str:
    template = """
    You are a sophisticated analysis tool developed to categorize system messages from COBOL programs running in an
    Atlas AIX environment. Your capabilities include identifying whether a message pertains to a compilation error,
    an execution error, or is part of normal operation logs. Here are the categories you need to focus on:

    - "compilation_error" for messages that indicate issues during the compilation phase, such as syntax errors or
     missing references.
    - "execution_error" for messages that reveal problems encountered while the program is executing, including runtime
    exceptions or logical errors.
    - "logs" for messages that are informational, reflecting the program's normal operations or diagnostics logs.

    Based on the description above, analyze the following COBOL program output from the Atlas AIX environment and
    determine its category. Your response should contain a single key "message_type" with the corresponding value as one
    of the categories ("compilation_error", "execution_error", "logs").

    Message for analysis:
    {atlas_answer}
    """

    return template
