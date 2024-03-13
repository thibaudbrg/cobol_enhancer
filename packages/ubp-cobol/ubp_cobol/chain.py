from langgraph.graph import END, StateGraph

from .common import GraphState
from .processing import process_directory, process_file
from .generation import critic_gen, new_gen, eval_decider

workflow = StateGraph(GraphState)

workflow.add_node("process_directory", process_directory)
workflow.add_node("process_file", process_file)
workflow.add_node("critic_gen", critic_gen)
workflow.add_node("new_gen", new_gen)

workflow.set_entry_point("process_directory")
workflow.add_edge("process_directory", "process_file")
workflow.add_edge("process_file", "critic_gen")
workflow.add_conditional_edges("critic_gen", eval_decider, {
    "re_gen": "new_gen",  # bad quality
    "start_next_file_process": "process_file",  # good quality
    "end": END # all files processed
})
workflow.add_edge("new_gen", "critic_gen")

app = workflow.compile()
