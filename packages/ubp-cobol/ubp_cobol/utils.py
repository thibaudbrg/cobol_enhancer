from termcolor import colored

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