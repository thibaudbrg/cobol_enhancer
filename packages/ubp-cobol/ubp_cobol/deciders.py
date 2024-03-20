from ubp_cobol.common import GraphState
from ubp_cobol.utils import print_heading, print_info, print_error, sanitize_output


def has_finished_generation_decider(state: GraphState) -> str:
    print_heading("FINISHED DECIDER")
    result = state["new_code"]
    code_block_delimiter = "```"
    if not result.strip().endswith(code_block_delimiter):
        return "not_finished"
    else:
        state["new_code"] = sanitize_output(result)
        return "finished"


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
