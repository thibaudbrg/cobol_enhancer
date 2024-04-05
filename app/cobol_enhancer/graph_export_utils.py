import networkx as nx
import plotly.graph_objects as go
from graphviz import Digraph
from langchain_core.runnables.graph import Graph, Edge


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


def export_graph_to_image(graph: Graph, output_directory: str, filename: str = "graph_advanced"):
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
    green_edges_label = ['human_check', 'send_file', 'sender', 'next_file', 'no_more_file', 'logs']
    green_edges_from_source = ['__start__', 'process_directory', 'analyze_next_file', 'generate', 'sender']
    # Add edges with customized colors
    for edge in graph.edges:
        label = edge.data if edge.data else ""
        # Determine color based on specific conditions
        if label in green_edges_label or edge.source in green_edges_from_source:
            color = '#33cc33'  # Dark green for specified steps
        else:
            color = '#cc3333'  # Dark red for other steps
        dot.edge(edge.source, edge.target, label=label, color=color, fontsize='10')

    # Export the graph to a file
    dot.render(filename=filename, directory=output_directory, view=True, cleanup=True)


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
