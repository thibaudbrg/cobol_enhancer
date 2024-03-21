from langgraph.graph import END, StateGraph

from .common import GraphState
from .deciders import human_review_decider, evaluate_quality_decider, \
    has_finished_all_files_decider
from .generation import critic_generation, new_generation, human_review
from .processing import process_directory, process_next_file
from .response_handlers import sender, receiver, handle_logs, message_type_decider

workflow = StateGraph(GraphState)

workflow.add_node("process_directory", process_directory)
workflow.add_node("process_next_file", process_next_file)
workflow.add_node("critic_generation", critic_generation)
workflow.add_node("new_generation", new_generation)
workflow.add_node("human_review", human_review)
workflow.add_node("sender", sender)
workflow.add_node("receiver", receiver)
workflow.add_node("handle_logs", handle_logs)

workflow.set_entry_point("process_directory")
workflow.add_edge("process_directory", "process_next_file")
workflow.add_edge("process_next_file", "critic_generation")
workflow.add_conditional_edges("critic_generation", evaluate_quality_decider, {
    "re_gen": "new_generation",
    "human_check": "human_review",
})
workflow.add_edge("new_generation", "critic_generation")
workflow.add_conditional_edges("human_review", human_review_decider, {
    "re_gen": "new_generation",
    "send_file": "sender",
})
workflow.add_edge("sender", "receiver")
workflow.add_conditional_edges("receiver", message_type_decider, {
    "compilation_error": "new_generation",
    "execution_error": "new_generation",
    "logs": "handle_logs"
})
workflow.add_conditional_edges("handle_logs", has_finished_all_files_decider, {
    "next_file": "process_next_file",
    "no_more_file": END
})

app = workflow.compile()
