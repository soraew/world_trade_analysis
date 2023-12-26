# %%
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import pickle as pkl
from warnings import filterwarnings
filterwarnings('ignore')

from hfuncs.preprocessing import *
from hfuncs.plotting import *
from hfuncs.graphs import *

# %%
# # load data
csvs_root= '../../csvs/'
data_root= '../../../../data/trade/BACI/'
data_file_name='top_ex_imp_2017_21_new.csv'

# ONLY EXPORTS
products = get_product_data(
    exports=True,
    imports=True,
    csvs_root=csvs_root,
    data_root=data_root,
    data_file_name=data_file_name,
)
countries = get_countries(data_root=data_root)
products = products[products['Level']==3]
products = products[products['economy_label'].isin(countries)]
products = products[products['partner_label'].isin(countries)]
products = products[products['partner_label'] != products['economy_label']]

# %%
# limiting exports to 764's exports
# that are larger than 1e5k(100million) USD
tele_product_code = '764'
tele_products = products[products['product']==tele_product_code]
tele_product_label = \
    tele_products['product_label'].values[0]

kusd_filter = 1e5
print(tele_products[tele_products['KUSD']>=kusd_filter]['KUSD'].sum()\
    /tele_products['KUSD'].sum())

tele_products = tele_products[tele_products['KUSD']>=kusd_filter]
tele_products = tele_products[tele_products['flow']==2]
# %%
year1 = 2017
year2 = 2018
year3 = 2019
kusd_filter = 1e5
tele_products = tele_products[['year', 'product', 'economy_label', 'partner_label', 'KUSD']]

tele_sub_G_17 = create_network(
    year1,
    tele_product_code,
    product_df=tele_products)
tele_sub_G_17 = filter_edges(tele_sub_G_17, min_kusd=kusd_filter)

tele_sub_G_18 = create_network(
    year2,
    tele_product_code,
    product_df=tele_products)
tele_sub_G_18 = filter_edges(tele_sub_G_18, min_kusd=kusd_filter)

tele_sub_G_19 = create_network(
    year2,
    tele_product_code,
    product_df=tele_products)
tele_sub_G_19 = filter_edges(tele_sub_G_19, min_kusd=kusd_filter)

# %%
def log_weight_scaler(weight):
    return np.log(np.log(np.log(weight + 1.0) + 1.0) + 1.0)

def log_scale_weights(G):
    tmp_G = G.copy()
    weights_dict = \
        nx.get_edge_attributes(tmp_G, 'weight')
    log_weights = \
        {edge: log_weight_scaler(weight) \
            for edge, weight in weights_dict.items()}
    nx.set_edge_attributes(tmp_G, log_weights, 'weight')
    return tmp_G
tele_sub_G_17 = log_scale_weights(tele_sub_G_17)
tmp_weights = \
    nx.get_edge_attributes(tele_sub_G_17, 'weight')
fig = px.histogram(list(tmp_weights.values()))
fig.show()

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
# FIGSIZE = (14, 14) # for Interactive
FIGSIZE = (7, 7) # for Term
# %%
year = 2017
tele_sub_G_tmp = create_network(
    year,
    tele_product_code,
    product_df=tele_products)
tele_sub_G_tmp = filter_edges(tele_sub_G_tmp, min_kusd=kusd_filter)

sub_G = tele_sub_G_tmp.copy()
# sub_G.remove_node('Latvia')
# sub_G.remove_node('Lithuania')
partition = get_community_partition(sub_G)
pos = community_layout(sub_G, partition)
fig, ax = plot_communities(sub_G, partition, pos, figsize=FIGSIZE)
plt.title(f'{year} {tele_product_code} Trade Network')
plt.show()

year = 2018
tele_sub_G_tmp = create_network(
    year,
    tele_product_code,
    product_df=tele_products)
tele_sub_G_tmp = filter_edges(tele_sub_G_tmp, min_kusd=kusd_filter)

sub_G = tele_sub_G_tmp.copy()
# sub_G.remove_node('Latvia')
# sub_G.remove_node('Lithuania')
partition = get_community_partition(sub_G)
pos = community_layout(sub_G, partition)
fig, ax = plot_communities(sub_G, partition, pos, figsize=FIGSIZE)
plt.title(f'{year} {tele_product_code} Trade Network')
plt.show()

year = 2019
tele_sub_G_tmp = create_network(
    year,
    tele_product_code,
    product_df=tele_products)
tele_sub_G_tmp = filter_edges(tele_sub_G_tmp, min_kusd=kusd_filter)

sub_G = tele_sub_G_tmp.copy()
# sub_G.remove_node('Latvia')
# sub_G.remove_node('Lithuania')
partition = get_community_partition(sub_G)
pos = community_layout(sub_G, partition)
fig, ax = plot_communities(sub_G, partition, pos, figsize=FIGSIZE)
plt.title(f'{year} {tele_product_code} Trade Network')
plt.show()

year = 2020
tele_sub_G_tmp = create_network(
    year,
    tele_product_code,
    product_df=tele_products)
tele_sub_G_tmp = filter_edges(tele_sub_G_tmp, min_kusd=kusd_filter)

sub_G = tele_sub_G_tmp.copy()
# sub_G.remove_node('Latvia')
# sub_G.remove_node('Lithuania')
partition = get_community_partition(sub_G)
pos = community_layout(sub_G, partition)
fig, ax = plot_communities(sub_G, partition, pos, figsize=FIGSIZE)
plt.title(f'{year} {tele_product_code} Trade Network')
plt.show()

year = 2021
tele_sub_G_tmp = create_network(
    year,
    tele_product_code,
    product_df=tele_products)
tele_sub_G_tmp = filter_edges(tele_sub_G_tmp, min_kusd=kusd_filter)

sub_G = tele_sub_G_tmp.copy()
# sub_G.remove_node('Latvia')
# sub_G.remove_node('Lithuania')
partition = get_community_partition(sub_G)
pos = community_layout(sub_G, partition)
fig, ax = plot_communities(sub_G, partition, pos, figsize=FIGSIZE)
plt.title(f'{year} {tele_product_code} Trade Network')
plt.show()

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
FIGSIZE = (14, 14)
years = (2017, 2019)
product_code = '764'
product_df = products
kusd_filter = 1e5

for year in years:
    tmp_G = create_network(
        year,
        product_code,
        product_df=product_df.copy())
    tmp_G = filter_edges(tmp_G, min_kusd=kusd_filter)
    tmp_G = log_scale_weights(tmp_G)

    partition = get_community_partition(tmp_G)
    pos = community_layout(tmp_G, partition)
    fig, ax = plot_communities(tmp_G, partition, pos, figsize=FIGSIZE)

    plt.title(f"{year} product:{product_code}", fontsize=25)
    plt.show()

# %%
def plot_communities_years(
        years,
        product_code,
        product_df,
        kusd_filter=1e5,
        figsize=(8, 8)):
    for year in years:
        tmp_G = create_network(
            year,
            product_code,
            product_df=product_df.copy())
        tmp_G = filter_edges(tmp_G, min_kusd=kusd_filter)
        tmp_G = log_scale_weights(tmp_G)

        partition = get_community_partition(tmp_G)
        pos = community_layout(tmp_G, partition)
        fig, ax = plot_communities(tmp_G, partition, pos, figsize=figsize)

        plt.title(f"{year} product:{product_code}", fontsize=25)
        plt.show()
# %%
FIGSIZE = (14, 14)
KUSD_FILTER = 1e5
YEARS = (2017, 2019)
PRODUCTS = [
    '764', # Telecommunication equipment, n.e.s. & parts, ...
    '776', # Cathode valves & tubes(semiconductors)
    '778', # Electrical machinery & apparatus, n.e.s.
]
# Telecommunication equipment, n.e.s. & parts, ...
for product in PRODUCTS:
    plot_communities_years(
        YEARS,
        product, # product_code
        products, # DataFrame
        kusd_filter=KUSD_FILTER,
        figsize=FIGSIZE)
