from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

from app.cobol_enhancer.common import WorkflowExit, MODEL_NAME
from app.cobol_enhancer.graph_export_utils import merge_deciders_for_printing, export_graph_to_image
from app.cobol_enhancer.utils import extract_copybooks, format_copybooks_for_display, print_heading
from app.cobol_enhancer.workflow import app


def test_workflow():
    """
    Test the full workflow by running the process_directory and process_file functions together.
    """

    inputs = {}

    # Run the application with the initialized inputs
    try:
        for output in app.stream(inputs):
            for key, value in output.items():
                print("\n---\n")
    except WorkflowExit:
        print("Workflow exited early as expected.")


def test_print_workflow():

    graph = merge_deciders_for_printing(app.get_graph())
    # Ensure the data directory exists

    #1st plot
    image_data = graph.draw_png()
    with open('data/graph_image.png', 'wb') as img_file:
        img_file.write(image_data)

    #2nd plot
    export_graph_to_image(graph, "data/", "graph_image_own")

def test_copy_parser():
    """
    Test the extract_copybooks function to ensure it correctly identifies copybook names in a COBOL file.
    """
    cobol_file_path = "data/input/DWGEX699.cob"
    with open(cobol_file_path, 'r') as file:
        code = file.read()

    copybooks = extract_copybooks(code)

    print(format_copybooks_for_display(copybooks))


def test_extender():
    session_id = "foo"

    def create_redis_history(session_id):
        return RedisChatMessageHistory(session_id, url="redis://localhost:6379")

    print_heading("EXTENDER")

    template = """
You are an AI and you talk to a human you answer everything that he asked but with the tone of this emotion: {emotion}.
"""

    model = ChatOpenAI(temperature=0, model=MODEL_NAME, streaming=True)

    prompt = ChatPromptTemplate.from_messages([
        ("system", template),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}")])

    chain = prompt | model | StrOutputParser()
    chain_with_history = RunnableWithMessageHistory(
        chain,
        create_redis_history,  # Use the lambda function here
        input_messages_key="question",
        history_messages_key="history",
    )

    config = {"configurable": {"session_id": session_id}}
    result = chain_with_history.invoke({"question": "Tell me a joke and put emojis", "emotion": "best dude friend but slow as the big lebowski"}, config=config)

    print(result)

    # After invoking, create an instance of RedisChatMessageHistory to print the history
    redis_history = create_redis_history(session_id)

    # Now retrieve and print the messages
    history_messages = redis_history.messages  # Adjusted based on actual implementation
    redis_history.clear()
    print("History:", history_messages)
