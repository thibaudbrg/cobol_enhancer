from langgraph.graph import END, StateGraph

from .common import GraphState
from .deciders import human_review_decider, evaluate_quality_decider, \
    has_finished_all_files_decider
from .generation import critic_generation, human_review, process_directory, generate, analyze_next_file
from .response_handlers import sender, receiver, handle_logs, message_type_decider

workflow = StateGraph(GraphState)

workflow.add_node("process_directory", process_directory)
workflow.add_node("analyze_next_file", analyze_next_file)
workflow.add_node("generate", generate)
workflow.add_node("critic_generation", critic_generation)
workflow.add_node("human_review", human_review)
workflow.add_node("sender", sender)
workflow.add_node("receiver", receiver)
workflow.add_node("handle_logs", handle_logs)

workflow.set_entry_point("process_directory")
workflow.add_edge("process_directory", "analyze_next_file")
workflow.add_edge("analyze_next_file", "generate")
workflow.add_edge("generate", "critic_generation")
workflow.add_conditional_edges("critic_generation", evaluate_quality_decider, {
    "re_gen": "generate",
    "human_check": "human_review",
})
workflow.add_conditional_edges("human_review", human_review_decider, {
    "re_gen": "generate",
    "send_file": "sender",
})
workflow.add_edge("sender", "receiver")
workflow.add_conditional_edges("receiver", message_type_decider, {
    "compilation_error": "generate",
    "execution_error": "generate",
    "logs": "handle_logs"
})
workflow.add_conditional_edges("handle_logs", has_finished_all_files_decider, {
    "next_file": "analyze_next_file",
    "no_more_file": END
})

app = workflow.compile()
