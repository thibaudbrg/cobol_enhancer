from termcolor import colored
import re, os


# Utility functions for UI
def print_heading(heading: str):
    print(colored(f"\n{heading}\n", 'cyan', attrs=['bold']))


def print_subheading(subheading: str):
    print(colored(f"{subheading}", 'yellow'))


def print_info(info: str):
    print(colored(f"{info}", 'green'))


def print_error(error: str):
    print(colored(f"{error}", 'red'))


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
    return copybooks


def format_copybooks_for_display(copybooks: dict) -> str:
    formatted_copybooks = []
    for name, content in copybooks.items():
        # Format each copybook's name and content
        formatted_copybooks.append(f"Copybook: {name}, Content: \n{content}\n")
    # Join all formatted copybooks into a single string
    return "\n".join(formatted_copybooks)