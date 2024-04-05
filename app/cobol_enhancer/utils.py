import difflib
import shutil

from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from termcolor import colored
import re
import os

from app.cobol_enhancer.common import GraphState


# Utility functions for UI
def print_heading(heading: str):
    print(colored(f"\n{heading}\n", 'cyan', attrs=['bold']))


def print_subheading(subheading: str):
    print(colored(f"{subheading}", 'yellow'))


def print_info(info: str):
    print(colored(f"{info}", 'green'))


def print_error(error: str):
    print(colored(f"{error}", 'red'))


def print_diff_line(line, width, prefix_length=2):
    # Adjust the line width for the prefix
    line_content = line[prefix_length:].rstrip()
    return f"{line_content:<{width - prefix_length}}"


def print_code_comparator(old_code: str, new_code: str) -> str:
    # Get terminal width and calculate half for side-by-side view
    terminal_width = shutil.get_terminal_size().columns
    half_terminal_width = terminal_width // 2

    # Split the code into lines for diffing
    old_code_lines = old_code.split('\n')
    new_code_lines = new_code.split('\n')

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


def sanitize_output(text: str, rm_opening: bool = True, rm_closing: bool = True):
    # Define the possible opening and closing delimiters
    opening_delimiters = ["```cobol", "```plaintext"]
    closing_delimiter = "```"

    # Check for opening delimiters and remove them if required
    for opening in opening_delimiters:
        if text.startswith(opening):
            if rm_opening:
                text = text[len(opening):]
            break

    # Check for closing delimiter and remove it if required
    if rm_closing and closing_delimiter in text:
        closing_index = text.rfind(closing_delimiter)
        text = text[:closing_index]

    return text.strip()


def extract_copybooks(cobol_file_content: str) -> dict:
    """
    Extracts the names and contents of all copybooks used in a COBOL file content string,
    accounting for lines where 'COPY' does not start at the beginning of the line.

    Args:
        cobol_file_content (str): The COBOL file content as a string.

    Returns:
        dict: A dictionary with copybook names as keys and their contents as values.
    """
    print("\n")
    copy_regex = re.compile(r'\bCOPY\s+(\S+)\.?')
    copybooks = {}
    lines = cobol_file_content.splitlines()
    for line in lines:
        matches = copy_regex.findall(line)
        for match in matches:
            # Remove potential trailing period
            copybook_name = match.rstrip('.')
            copybook_path = os.path.join("data/input/copy", copybook_name)
            try:
                with open(copybook_path, 'r', encoding='utf-8') as copybook_file:
                    copybooks[copybook_name] = copybook_file.read()
            except FileNotFoundError:
                print(f"Copybook {copybook_name} not found at {copybook_path}")
    print("\n")
    return copybooks


def format_copybooks_for_display(copybooks: dict) -> str:
    formatted_copybooks = []
    for name, content in copybooks.items():
        # Format each copybook's name and content
        formatted_copybooks.append(f"Copybook: {name}, Content: \n{content}\n")
    # Join all formatted copybooks into a single string
    return "\n".join(formatted_copybooks)


def get_previous_critic_description(state: GraphState) -> str:
    # Ensure 'critic' exists in state, is a dictionary, and has a 'description' key
    if "critic" in state and isinstance(state["critic"], dict) and "description" in state["critic"]:
        return state["critic"]["description"]
    else:
        return ""


def filename_tab_completion(text, state):
    # List all file names in data/input/, filtering by the current input text
    files = [f for f in os.listdir("data/input/") if f.startswith(text)]
    # Return the state-th file name if it exists, appending a space for convenience
    return (files[state] + " ") if state < len(files) else None


def generate_code_with_history(state, function_name, template, model, variables):
    redis_url = os.environ.get('REDIS_URL')
    if redis_url is None:
        raise ValueError("The REDIS_URL environment variable is not set.")
    session_id = f"{function_name}_{state['filename']}"

    def redis_history(id):
        return RedisChatMessageHistory(id, url=redis_url)

    # Clear the history before starting to avoid any potential issues
    redis_history(session_id).clear()

    prompt = ChatPromptTemplate.from_messages([
        ("system", template),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}")])

    chain_with_history = RunnableWithMessageHistory(
        prompt | model | StrOutputParser(),
        redis_history,
        input_messages_key="question",
        history_messages_key="history",
    )

    config = {"configurable": {"session_id": session_id}}

    code_block_delimiter = "```"
    is_first_iteration = True
    final_output_accumulated = ""
    while True:
        # Set "question" based on whether it's the first iteration
        question_value = "" if is_first_iteration else "continue"

        result = chain_with_history.invoke({
            "question": question_value,
            **variables  # Unpack additional_variables into the outer dictionary
        }, config=config)

        current_output = sanitize_output(result, True, False)

        # Always append to the final_output_accumulated to accumulate all iterations
        if is_first_iteration:
            final_output_accumulated = current_output
            is_first_iteration = False
        else:
            final_output_accumulated += current_output

        # Check if the result meets the condition to exit the loop
        if final_output_accumulated.strip().endswith(code_block_delimiter) and "Continuation" not in result:
            # Final sanitization and adjustment if necessary before breaking the loop
            redis_history(session_id).clear()
            return sanitize_output(final_output_accumulated)
        else:
            print_info("Extending the output with another iteration...")
