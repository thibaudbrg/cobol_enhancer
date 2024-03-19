from langgraph.graph import END, StateGraph

from .common import GraphState
from .processing import process_directory, process_file, extender, finished
from .generation import critic_gen, new_gen, eval_decider
from .response_handlers import sender, receiver, handle_logs, determine_message_type

workflow = StateGraph(GraphState)

workflow.add_node("process_directory", process_directory)
workflow.add_node("process_file", process_file)
workflow.add_node("critic_gen", critic_gen)
workflow.add_node("new_gen", new_gen)
workflow.add_node("extender", extender)
workflow.add_node("sender", sender)
workflow.add_node("receiver", receiver)
workflow.add_node("handle_logs", handle_logs)

workflow.set_entry_point("process_directory")
workflow.add_edge("process_directory", "process_file")
workflow.add_conditional_edges("process_file", finished, {
    "not_finished": "extender",
    "finished": "critic_gen"
})
workflow.add_conditional_edges("extender", finished, {
    "not_finished": "extender",
    "finished": "critic_gen"
})
workflow.add_conditional_edges("critic_gen", eval_decider, {
    "re_gen": "new_gen",  # bad quality
    "send_file": "sender",  # good quality
    # "end": END # all files processed
})
workflow.add_edge("sender", "receiver")
workflow.add_conditional_edges("receiver", determine_message_type, {
    "compilation_error": "new_gen",
    "execution_error": "new_gen",
    "logs": "handle_logs"
})
workflow.add_edge("handle_logs", END)
workflow.add_edge("new_gen", "critic_gen")

app = workflow.compile()
