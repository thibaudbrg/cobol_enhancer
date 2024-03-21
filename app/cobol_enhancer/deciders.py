from app.cobol_enhancer.common import GraphState
from app.cobol_enhancer.utils import print_heading, print_info, print_error


def human_review_decider(state: GraphState):
    print_heading("HANDLE HUMAN REVIEW")
    print_info(f"Human review decision: {state['human_decision']}")

    if state["human_decision"] == "yes":
        return "send_file"
    else:
        return "re_gen"


def evaluate_quality_decider(state: GraphState):
    print_heading("EVALUATION DECIDER")
    grade = state["critic"]["grade"]

    if grade == "good":
        return "human_check"
    else:
        print_error("Critic has identified issues. Initiating regeneration...")
        return "re_gen"


def has_finished_all_files_decider(state: GraphState):
    print_heading("FINISHED ALL FILES DECIDER")
    if state["files_to_process"]:
        return "next_file"
    else:
        print_info("All files have been processed.")
        print_heading("END")
        return "no_more_file"
