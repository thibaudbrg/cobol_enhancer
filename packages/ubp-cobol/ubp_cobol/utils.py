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

def sanitize_output(text: str):
    possible_delimiters = ["```cobol", "```plaintext"]
    for delimiter in possible_delimiters:
        if delimiter in text:
            _, after = text.split(delimiter)
            code = after.split("```")[0]
            return code.strip()
    return text.strip()