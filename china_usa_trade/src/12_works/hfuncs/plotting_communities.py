import pandas as pd
import numpy as np
import plotly.express as px
import networkx as nx
import matplotlib.pyplot as plt

from hfuncs.graphs import *
from hfuncs.preprocessing import *

# %%
def community_layout(g, partition):
    """
    Compute the layout for a modular graph.
    Arguments:
    ----------
    g -- networkx.Graph or networkx.DiGraph instance
        graph to plot
    partition -- dict mapping int node -> int community
        graph partitions
    Returns:
    --------
    pos -- dict mapping int node -> (float x, float y)
        node positions
    """
    # partition is dict of form: {ni: ci, ...}
    pos_communities_nodes, pos_communities, hypergraph = \
        _position_communities(g, partition, scale=4.)

    pos_nodes = _position_nodes(g, partition, scale=1., k=0.9)

    # COMBINE POSITIONS!!!!!
    pos = dict()
    for node in g.nodes():
        pos[node] = pos_communities_nodes[node] + pos_nodes[node]

    return pos

def _position_communities(g, partition, **kwargs):
    # CREATE A WEIGHTED GRAPH, IN WHICH EACH NODE CORRESPONDS TO A COMMUNITY,
    # AND EACH EDGE WEIGHT TO THE NUMBER OF EDGES BETWEEN COMMUNITIES

    # returns dict of form: {(ci, cj): [(ni, nj), ...], ...}
    between_community_edges = _find_between_community_edges(g, partition)

    communities = set(partition.values())
    hypergraph = nx.DiGraph()
    hypergraph.add_nodes_from(communities)
    # below is the key component of this function
    for (ci, cj), edges in between_community_edges.items():
        hypergraph.add_edge(ci, cj, weight=len(edges))

    # find layout for communities
    pos_communities = nx.spring_layout(hypergraph, **kwargs)

    # set node positions to position of community
    pos = dict()
    for node, community in partition.items():
        pos[node] = pos_communities[community]

    return pos, pos_communities, hypergraph

# just returns nodes that are between communities
def _find_between_community_edges(g, partition):
    edges = dict()
    for (ni, nj) in g.edges():
        ci = partition[ni]
        cj = partition[nj]
        if ci != cj:
            try:
                edges[(ci, cj)] += [(ni, nj)]
            except KeyError:
                edges[(ci, cj)] = [(ni, nj)]
    return edges

# positions nodes within communities.
def _position_nodes(g, partition, **kwargs):
    communities = dict()
    for node, community in partition.items():
        try:
            communities[community] += [node]
        except KeyError:
            communities[community] = [node]

    pos = dict()
    for ci, nodes in communities.items():
        subgraph = g.subgraph(nodes)
        pos_subgraph = nx.spring_layout(subgraph, **kwargs)
        pos.update(pos_subgraph)

    return pos

# for each node, get the community it belongs to
def get_community_partition(sub_G):
    communities = nx.community.greedy_modularity_communities(sub_G)
    communities = list(communities)
    partition = dict()
    for i, community in enumerate(communities):
        for country in community:
            partition[country] = i
    return partition

# %%
def plot_communities(sub_G, partition, pos, figsize=(8, 8)):
    fig, ax = plt.subplots(figsize=figsize)
    # position = nx.circular_layout(sub_G, scale=2.5)
    weights_dict = \
        scale_weights(sub_G, scaler=1.0)
    weights = \
        np.fromiter(weights_dict.values(), dtype=float)
    log_weights = \
        1/4*np.log(weights+1.0)

    communities = set(partition.values())
    cmap = plt.get_cmap('Set1')
    colors = \
        [cmap(i) for i in np.linspace(0.2, 0.7, len(communities))]
    for i, community in enumerate(communities):
        sub_G_tmp = sub_G.subgraph(
            [node for node in sub_G.nodes() if partition[node]==community])
        nx.draw_networkx_nodes(
            sub_G_tmp,
            pos=pos,
            node_color=colors[i],
            ax=ax,)
    nx.draw_networkx_labels(
        sub_G,
        labels=dict(zip(sub_G.nodes(), sub_G.nodes())),
        pos=pos,
        font_size=11,
        ax=ax,)
    nx.draw_networkx_edges(
        sub_G, pos,
        edgelist=sub_G.edges(),
        width=log_weights,
        connectionstyle="arc3,rad=0.1",
        ax=ax,)
    # plt.show()
    return fig, ax

# %%
def plot_hist(year, product_code, sub_G):
    tmp_weights = \
        nx.get_edge_attributes(sub_G, 'weight')
    fig = px.histogram(list(tmp_weights.values()))
    fig.update_layout(
        title=f'{year} {product_code} Trade Network',
    )
    fig.show()
# %%
def plot_communities_years(
        years,
        product_code,
        product_df,
        kusd_filter=1e5,
        figsize=(8, 8),
        label_columns=['Code_economy', 'Code_partner']):
    for year in years:
        tmp_G = create_network(
            year,
            product_code,
            product_df=product_df.copy(),
            label_columns=label_columns)
        tmp_G = filter_edges(tmp_G, min_kusd=kusd_filter)
        tmp_G = log_scale_weights(tmp_G)

        partition = get_community_partition(tmp_G)
        pos = community_layout(tmp_G, partition)
        fig, ax = plot_communities(tmp_G, partition, pos, figsize=figsize)
        flows = product_df.flow.unique()

        plt.title(f"flow: {flows}, {year} product:{product_code}", fontsize=25)
        plt.show()

# %% basic plot
def plot_basic_communities(G, partition, figsize=(8, 8)):
    position = nx.spring_layout(G, k=0.9, iterations=50)
    fig, ax = plt.subplots(figsize=figsize)
    cmap = plt.get_cmap('Set1')
    communities = set(partition.values())
    colors = \
        [cmap(i) for i in np.linspace(0.2, 0.7, len(communities))]
    for i, community in enumerate(communities):
        nodes = [node for node in G.nodes() if partition[node]==community]
        G_tmp = G.subgraph(
            nodes=nodes)
        nx.draw_networkx_nodes(
            G_tmp,
            pos=position,
            node_color=colors[i],
            ax=ax,)
    nx.draw_networkx_labels(
        G,
        labels=dict(zip(G.nodes(), G.nodes())),
        pos=position,
        font_size=11,
        ax=ax,)
    nx.draw_networkx_edges(
        G, position,
        edgelist=G.edges(),
        width=0.2,
        ax=ax)
    plt.show()

# %% community detection
def get_louvain_partition(G):
    communities = nx.community.louvain_communities(G)
    communities = list(communities)
    partition = dict()
    for i, community in enumerate(communities):
        for country in community:
            partition[country] = i
    return partition

def plot_communities_geo(
        product_partition,
        iso_corr,
        TYPE='Telecommunication equipment',
        YEAR=2017,
        show=False):
    comms = set(product_partition.values())
    ncomms = len(comms)
    tmp = pd.DataFrame(columns=['iso2', 'community'])

    # list of list of country codes
    for comm in comms:
        sublist = \
            [code for code in product_partition.keys() if \
                product_partition[code] == comm]
        community_arr = [str(comm)] * len(sublist)
        tmp_tmp = pd.DataFrame({'iso2': sublist, 'community': community_arr})
        tmp = pd.concat([tmp, tmp_tmp], axis=0)

    # merge iso2 and iso3
    tmp = pd.merge(tmp, iso_corr, on='iso2', how='left')
    fig = px.choropleth(
        locations=tmp['iso3'],
        color=tmp['community'],
        color_discrete_sequence=px.colors.qualitative.Set1[:ncomms],
        locationmode='ISO-3',)
    if TYPE=='Telecommunication equipment' or TYPE=='RTA' or TYPE=='Total' and YEAR:
        title = f'{TYPE} communities in {YEAR}'
    else:
        title = f'{TYPE} communities'
    fig.update_layout(
        title_text=title,
        legend_title_text='community',
        geo=dict(
            showframe=False,
            showcoastlines=False,
            projection_type='equirectangular'),
        margin={'b':0}
        )
    if show:
        fig.show()
    return fig
