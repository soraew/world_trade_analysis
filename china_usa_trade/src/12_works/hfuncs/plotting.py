import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import matplotlib.pyplot as plt

from hfuncs.graphs import *
from hfuncs.preprocessing import scale_weights


def plot_directed_network(
        G_sub,
        select_countries,
        position,
        weights,
        figsize):
    fig, ax = plt.subplots(figsize=figsize)
    nx.draw_networkx_nodes(
        G_sub,
        pos=position,
        node_color='lightblue',
        # node_size=node_sizes,
        ax=ax,)
    nx.draw_networkx_labels(
        G_sub,
        labels=dict(zip(select_countries, select_countries)),
        pos=position,
        # bbox = dict(facecolor = "skyblue"),
        font_size=11,
        ax=ax,)
    nx.draw_networkx_edges(
        G_sub, position,
        edgelist=G_sub.edges(),
        width=weights,
        connectionstyle="arc3,rad=0.1",
        ax=ax)
    # plt.show()
    return fig, ax

def plot_subG(subG, scaler=1.0, min_kusd=5e4, countries=False, figsize=(14, 14)):
    if countries:
        subG = filter_nodes(subG, countries)
    if min_kusd:
        subG = filter_edges(subG, min_kusd=min_kusd)

    position = nx.circular_layout(subG, scale=1.5)
    weights_dict = \
        scale_weights(
        subG,
        scaler=scaler)
    weights = \
        list(weights_dict.values())
    fig, ax = plot_directed_network(
        subG,
        subG.nodes(),
        position,
        weights,
        figsize)
    return fig, ax

# # create edges
# pos = nx.spring_layout(G, k=1)
# # pos = nx.kamada_kawai_layout(G)
# # pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
#
# edge_x = []
# edge_y = []
# for edge in G.edges():
#     x0 = pos[edge[0]][0]
#     y0 = pos[edge[0]][1]
#     x1 = pos[edge[1]][0]
#     y1 = pos[edge[1]][1]
#
#     edge_x.append(x0)
#     edge_x.append(x1)
#     edge_x.append(None)
#     edge_y.append(y0)
#     edge_y.append(y1)
#     edge_y.append(None)
#
# edge_trace = go.Scatter(
#     x=edge_x, y=edge_y,
#     line=dict(width=0.5, color='#888'),
#     hoverinfo='none',
#     mode='lines')
#
# # create nodes
# node_x = []
# node_y = []
# for node in G.nodes():
#     x, y = pos[node][0], pos[node][1]
#     node_x.append(x)
#     node_y.append(y)
#
# node_trace = go.Scatter(
#     x=node_x, y=node_y,
#     mode='markers',
#     hoverinfo='text',
#     marker=dict(
#         showscale=True,
#         colorscale='YlGnBu',
#         reversescale=True,
#         color=[],
#         size=10,
#         colorbar=dict(
#             thickness=15,
#             title='Node Connections',
#             xanchor='left',
#             titleside='right'
#         ),
#         line_width=2))
#     
# # color nodes
# node_adjacencies = []
# node_text = []
# for node, adjacencies in enumerate(G.adjacency()):
#     node_adjacencies.append(len(adjacencies[1]))
#     # node_text.append('# of connections: '+str(len(adjacencies[1])))
#     node_text.append(adjacencies[0])
#
# node_trace.marker.color = node_adjacencies
# node_trace.text = node_text
#
# # create network graph
# fig = go.Figure(data=[edge_trace, node_trace],
#                 layout=go.Layout(
#                     title='Network Graph of Product 764',
#                     titlefont_size=16,
#                     showlegend=False,
#                     hovermode='closest',
#                     margin=dict(b=20,l=5,r=5,t=40),
#                     annotations=[dict(
#                         text="",
#                         showarrow=False,
#                         xref="paper", yref="paper",
#                         x=0.005, y=-0.002 ) ],
#                     xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), 
#                     yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
#                     )
# fig.show()
#
