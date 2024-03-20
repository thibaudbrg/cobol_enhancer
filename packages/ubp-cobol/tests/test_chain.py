import pytest
import os
from tempfile import TemporaryDirectory

from ubp_cobol.common import WorkflowExit
from ubp_cobol.workflow import process_directory, GraphState, app, merge_deciders_for_printing, export_graph_to_image, \
    convert_graph_to_plotly_figure
from IPython.display import Image
from ubp_cobol.utils import extract_copybooks, format_copybooks_for_display


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
    image_data = merge_deciders_for_printing(app.get_graph()).draw_png()
    with open('data/graph_image.png', 'wb') as img_file:
        img_file.write(image_data)

    export_graph_to_image(merge_deciders_for_printing(app.get_graph()), "data/graph")
    fig = convert_graph_to_plotly_figure(merge_deciders_for_printing(app.get_graph()))
    fig.show()

def test_copy_parser():
    """
    Test the extract_copybooks function to ensure it correctly identifies copybook names in a COBOL file.
    """
    cobol_file_path = "data/input/DWGEX699.cob"
    with open(cobol_file_path, 'r') as file:
        code = file.read()

    copybooks = extract_copybooks(code)

    print(format_copybooks_for_display(copybooks))
