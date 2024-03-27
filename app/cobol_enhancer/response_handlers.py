import os

from langchain import hub
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .common import GraphState, MODEL_NAME
from .utils import print_heading, print_info, print_error


def sender(state: GraphState) -> GraphState:
    print_heading("SENDER")
    # Simulate sending the file to FTP (in real use, replace this with actual FTP send logic)
    print_info(f"File {state['filename']} sent to FTP.")
    return state


def receiver(state: GraphState) -> GraphState:
    print_heading("RECEIVER")
    print("Enter the multi-line message from Atlas (compilation error, execution error, or logs).")
    print("Enter 'END' on a new line when you are done.")

    lines = []
    while True:
        line = input()
        if line == "END":  # Sentinel value to stop input
            break
        lines.append(line)

    # Join all lines into a single string, separated by newline characters
    state["atlas_answer"] = '\n'.join(lines)
    return state


def message_type_decider(state: GraphState) -> str:
    print_heading("DETERMINE MESSAGE TYPE")

    # Prepare the prompt and the model for calling OpenAI
    # prompt = "Analyze the following message and determine if
    # it's a compilation error, execution error, or logs:\n\n" + state["atlas_answer"]
    prompt = hub.pull("thibaudbrg/cobol-determine-message")
    model = ChatOpenAI(temperature=0, model=MODEL_NAME, streaming=True)

    # Define the Pydantic model for the message type result
    class MessageTypeResult(BaseModel):
        message_type: str = Field(
            description="The type of the message: 'compilation_error', 'execution_error', or 'logs'.")

    chain = prompt | model.with_structured_output(MessageTypeResult)

    try:
        message_pydantic = chain.invoke({"atlas_answer": state["atlas_answer"]})
        message = message_pydantic.dict()["message_type"]

        print_info(f"Determined message type: {message}")

        state["atlas_message_type"] = message

        # Corrected comparisons to check the value of message_type
        if message == "compilation_error":
            print_info("The message indicates a compilation error.")
            return "compilation_error"
        elif message == "execution_error":
            print_info("The message indicates an execution error.")
            return "execution_error"
        else:  # "logs"
            print_info("The message is part of the logs.")
            return "logs"
    except Exception as e:
        print_error(f"Error determining message type: {e}")
        return "error"  # Fallback in case of failure


def handle_logs(state: GraphState) -> GraphState:
    print_heading("LOGS HANDLER")
    print_info(state["atlas_answer"])

    current_file = state["files_to_process"].pop(0)
    output_file_path = current_file.replace("data/input/", "data/output/")
    justification_file_path = output_file_path.replace('.cob', '_justification.md')
    log_file_path = output_file_path.replace('.cob', '_logs.txt')

    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    with open(output_file_path, 'w') as file:
        file.write(state["new_code"])
    print_info(f"Saved improved code to: {output_file_path}")

    with open(justification_file_path, 'w') as jfile:
        jfile.write(state["critic"]["description"])
    print_info(f"Saved justification to: {justification_file_path}")

    with open(log_file_path, 'w') as log_file:
        log_file.write(state["atlas_answer"])
    print_info(f"Saved logs to: {log_file_path}")

    # Clear state for the next iteration or conclusion
    state["old_code"] = ""
    state["previous_last_gen_code"] = ""
    state["new_code"] = ""
    state["human_decision"] = ""
    state["specific_demands"] = ""
    state["filename"] = ""
    state["original_critic"] = {}
    state["critic"] = {}
    state["copybooks"] = {}
    state["atlas_answer"] = ""
    state["atlas_message_type"] = ""

    return state
