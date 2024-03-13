import pytest
import os
from tempfile import TemporaryDirectory
from ubp_cobol.chain import process_directory, GraphState, app

#@pytest.fixture
#def cobol_project_directory():
#    """
#    Creates a temporary directory with a simulated COBOL project structure, including .cob, .pco files, and a copy directory.
#    """
#    with TemporaryDirectory() as tmpdirname:
#        # Simulate COBOL and PCO files
#        source_file_paths = [
#            os.path.join(tmpdirname, "ABORT.cob"),
#            os.path.join(tmpdirname, "DBACCESS.pco"),
#            os.path.join(tmpdirname, "DWGEX699.cob"),
#            os.path.join(tmpdirname, "READCARD.cob"),
#        ]
#        for file_path in source_file_paths:
#            with open(file_path, "w") as f:
#                f.write("IDENTIFICATION DIVISION.\nPROGRAM-ID. Sample.\n")
#
#        # Simulate COPYBOOK directory
#        copybook_dir = os.path.join(tmpdirname, "copy")
#        os.makedirs(copybook_dir, exist_ok=True)
#        copybook_path = os.path.join(copybook_dir, "A15000")
#        with open(copybook_path, "w") as f:
#            f.write("COPY A15000.\n")
#
#        yield tmpdirname
#
#def test_process_directory(cobol_project_directory):
#    """
#    Test the process_directory function to ensure it correctly identifies .cob and .pco files and populates the state.
#    """
#    initial_state = GraphState(files_to_process=[], file_metadata={})
#    updated_state = process_directory(initial_state, cobol_project_directory)
#
#    print(updated_state)
#    assert len(updated_state["files_to_process"]) == 3, "Should find four source files (.cob)"
#    assert all(file_path.endswith((".cob", ".pco")) for file_path in updated_state["files_to_process"]), "All files should have .cob or .pco extension"
#    assert all(file_path in updated_state["file_metadata"] for file_path in updated_state["files_to_process"]), "Each file should have a metadata entry"
#    # You could extend this test to check for specific metadata related to COPYBOOK dependencies if your implementation supports it.


def test_workflow():
    """
    Test the full workflow by running the process_directory and process_file functions together.
    """
    # Assuming your COBOL files are located in a directory called "cobol_files"
    directory_path = ""

    # Initialize the inputs with the directory path
    inputs = {}

    # Run the application with the initialized inputs
    for output in app.stream(inputs):
        for key, value in output.items():

            print("\n---\n")
