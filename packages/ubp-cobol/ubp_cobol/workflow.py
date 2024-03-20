from typing import Optional
from graphviz import Digraph
import plotly.graph_objects as go
import networkx as nx

from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.graph import Graph, Edge
from langgraph.graph import END, StateGraph

from .common import GraphState
from .processing import process_directory, process_next_file, extender
from .generation import critic_generation, new_generation, human_review
from .response_handlers import sender, receiver, handle_logs, message_type_decider
from .deciders import has_finished_generation_decider, human_review_decider, evaluate_quality_decider, \
    has_finished_all_files_decider

workflow = StateGraph(GraphState)

workflow.add_node("process_directory", process_directory)
workflow.add_node("process_next_file", process_next_file)
workflow.add_node("critic_generation", critic_generation)
workflow.add_node("new_generation", new_generation)
workflow.add_node("extender", extender)
workflow.add_node("human_review", human_review)
workflow.add_node("sender", sender)
workflow.add_node("receiver", receiver)
workflow.add_node("handle_logs", handle_logs)

workflow.set_entry_point("process_directory")
workflow.add_edge("process_directory", "process_next_file")
workflow.add_conditional_edges("process_next_file", has_finished_generation_decider, {
    "not_finished": "extender",
    "finished": "critic_generation"
})
workflow.add_conditional_edges("extender", has_finished_generation_decider, {
    "not_finished": "extender",
    "finished": "critic_generation"
})
workflow.add_conditional_edges("critic_generation", evaluate_quality_decider, {
    "re_gen": "new_generation",
    "human_review": "human_review",
})
workflow.add_conditional_edges("new_generation", has_finished_generation_decider, {
    "not_finished": "extender",
    "finished": "critic_generation"
})
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

def merge_deciders_for_printing(graph: Graph) -> Graph:
    # Step 1: Identify deciders and their targets with labels
    decider_targets = {}
    for edge in graph.edges:
        if "decider" in edge.source:
            # Initialize if not exists
            if edge.source not in decider_targets:
                decider_targets[edge.source] = {}
            decider_targets[edge.source][edge.data] = (edge.target, edge.data)

    # Step 2: Redirect edges to decider targets with labels and remove decider nodes
    new_edges = []
    for edge in graph.edges:
        if edge.target in decider_targets:
            # Redirect edges through decider with labels
            for decision, (target, label) in decider_targets[edge.target].items():
                new_edges.append(Edge(edge.source, target, label))
        elif "decider" not in edge.source:
            # Keep non-decider edges with their original labels
            new_edges.append(edge)

    # Step 3: Remove decider nodes
    new_nodes = {node_id: node for node_id, node in graph.nodes.items() if "decider" not in node_id}

    # Return new graph with merged deciders and labels on edges
    return Graph(new_nodes, new_edges)


def export_graph_to_image(graph: Graph, output_filename: str = "graph_advanced"):
    dot = Digraph(comment='Workflow Graph', format='png')

    # Increase the DPI for higher image quality
    dot.attr(dpi='300')

    # Graph style attributes - Set layout direction to top-to-bottom
    dot.attr(rankdir='TB', size='15')

    # Default Node style attributes
    dot.attr('node', shape='ellipse', style='filled', color='#999999', fontname='Helvetica')

    # Specific styles for start and end nodes
    dot.node('__start__', '__start__', style='filled', fillcolor='#99cc99')  # Light green for start
    dot.node('__end__', '__end__', style='filled', fillcolor='#cc99cc')  # Light purple for end

    # Add non-special nodes with a loop for customization
    for node_id, node in graph.nodes.items():
        if node_id not in ['__start__', '__end__']:
            label = node_id.replace('_', ' ').title()
            dot.node(node_id, label, fillcolor='#ffcccc')  # Light red for other nodes

    # Define edges with specific conditions for green color
    green_edges = ['human_review', 'sender', 'handle_logs', 'next_file']

    # Add edges with customized colors
    for edge in graph.edges:
        label = edge.data if edge.data else ""
        # Determine color based on specific conditions
        if label in green_edges or edge.target in green_edges or edge.source in green_edges:
            color = '#33cc33'  # Dark green for specified steps
        else:
            color = '#cc3333'  # Dark red for other steps
        dot.edge(edge.source, edge.target, label=label, color=color, fontsize='10')

    # Export the graph to a file
    dot.render(output_filename, view=True)


def convert_graph_to_plotly_figure(graph: Graph) -> go.Figure:
    # Create a directed graph with NetworkX
    G = nx.DiGraph()

    # Add nodes and edges to the NetworkX graph
    for node_id in graph.nodes:
        G.add_node(node_id)
    for edge in graph.edges:
        G.add_edge(edge.source, edge.target)

    # Apply a layout algorithm to position the nodes. Let's try a circular layout for a change.
    pos = nx.circular_layout(G)

    # Prepare the edge traces
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    # Add edges to the Plotly graph
    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=2, color='grey'), hoverinfo='none', mode='lines')

    # Prepare the node traces
    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    # Add nodes to the Plotly graph
    node_trace = go.Scatter(x=node_x, y=node_y, mode='markers+text', hoverinfo='text', text=list(G.nodes()),
                            marker=dict(showscale=False, color='blue', size=10), textposition="bottom center")

    # Create a Plotly figure
    fig = go.Figure(data=[edge_trace, node_trace], layout=go.Layout(showlegend=False, hovermode='closest',
                                                                    margin=dict(b=0, l=0, r=0, t=0),
                                                                    xaxis=dict(showgrid=False, zeroline=False,
                                                                               showticklabels=False),
                                                                    yaxis=dict(showgrid=False, zeroline=False,
                                                                               showticklabels=False)))
    return fig
