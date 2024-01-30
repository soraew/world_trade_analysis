# %%
import numpy as np
import pandas as pd
import igraph as ig
import networkx as nx
import plotly.express as px
import matplotlib.pyplot as plt
from sklearn.metrics import normalized_mutual_info_score as NMI
import pickle as pkl
import itertools
import time

from warnings import filterwarnings
filterwarnings('ignore')

from hfuncs.preprocessing import *
from hfuncs.plotting import *
from hfuncs.graphs import *
from hfuncs.plotting_communities import *
from hfuncs.rta import *
from hfuncs.dist import *
from hfuncs.alliance import *

# %% PARAMETERS
show = False
only_nmis = True
non_allied_countries = \
    ['HK', 'MO', 'TW', 'VN', 'SG', 'TH', 'SE', 'CH', 'ID']
YEAR = 2017
use_igraph = False

# %% for loading data
csvs_root= '../../csvs/'
git_csvs_root = '../../csvs_git/'
data_root= '../../../../data/trade/BACI/'
images_root = 'images/'
data_file_name='total_764_2016_21.csv'
# for plotting on map
iso_corr = \
    pd.read_csv(
        git_csvs_root+'countries_iso2to3.csv',
        encoding="ISO-8859-1",
        keep_default_na=False) 

# %% functions
def process_rta(csvs_root='../../csvs/',
                git_csvs_root='../../csvs_git/'):
    rta = pd.read_csv(csvs_root + 'AllRTAs_new.csv')
    tmp_rta = preprocess_rta(rta)
    with open(git_csvs_root+'abbv_rta_dict.pkl', 'rb') as f:
        abbv_rta_dict = pkl.load(f)
    tmp_rta_new = abbv_to_countries(tmp_rta, abbv_rta_dict)\
        .reset_index(drop=True)
    return tmp_rta_new
# preprocess for year and create rta_year_G
def get_rta_year_G(tmp_rta_new,
                   YEAR=2017,
                   git_csvs_root='../../csvs_git/'):
    rta_to_country_codes = \
        pd.read_csv(git_csvs_root + 'rta_to_country_codes.csv')
    rta_year = get_rta_year(tmp_rta_new, str(YEAR), git_csvs_root)
    rta_country_codes_year, country_codes_per_rta_year = \
        get_country_codes_per_RTA(rta_year, rta_to_country_codes)
    rta_year_G = \
        create_rta_network(rta_country_codes_year, country_codes_per_rta_year, weighted=True)
    return rta_year_G
# preprocess and create dist_G
def get_dist_G(csvs_root='../../csvs/', git_csvs_root='../../csvs_git/'):
    dist_inv = pd.read_csv(git_csvs_root + 'dist_inv.csv')
    dist_G = get_dist_network(dist_inv)
    return dist_G
# get louvain partitions
def get_louvain_orig_partition(G):
    start_time = time.time()
    communities_orig = nx.community.louvain_communities(G)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print('louvain:elapsed_time: ', elapsed_time)
    communities = list(communities_orig)
    partition = dict()
    for i, community in enumerate(communities):
        for country in community:
            partition[country] = i
    return partition, communities_orig
def get_greedy_orig_partition(G):
    start_time = time.time()
    communities_orig = nx.community.greedy_modularity_communities(G)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print('greedy:elapsed_time: ', elapsed_time)
    communities = list(communities_orig)
    partition = dict()
    for i, community in enumerate(communities):
        for country in community:
            partition[country] = i
    return partition, communities_orig

# %% stuff to run once(not every year)
# load and preprocess PRODUCT data
products, country_df = preprocess_products(
    exports=False,
    imports=True,
    csvs_root=csvs_root,
    data_root=data_root,
    data_file_name=data_file_name,)
products = products.dropna(subset=['Code_economy', 'Code_partner']) # limit to countries
products = products[products['partner_label'] != products['economy_label']]
# load and preprocess RTA data(process for each year later)
tmp_rta_new = process_rta(csvs_root, git_csvs_root)
tmp_rta_new.set_index('RTA ID', inplace=True)
tmp_rta_new.sort_index(inplace=True)

# %% stuff to run every year
# PRODUCT
product_G = create_network(
    YEAR, '764', products, ['Code_economy', 'Code_partner'])
total_G = create_network( YEAR, 'TOTAL',
    products[products['KUSD'] > 0], ['Code_economy', 'Code_partner'])
# RTA
rta_year_G = get_rta_year_G(tmp_rta_new, YEAR, git_csvs_root)
# ALLIANCE and DIST
if YEAR == 2017:
    # ALLIANCE
    v4 = pd.read_csv(csvs_root + 'version41_csv/alliance_v41_by_member.csv')
    v4_to_products = pd.read_csv(git_csvs_root + 'v4_to_products.csv')
    v4_active_new = preprocess_alliances(v4, v4_to_products)
    alliance_lists = get_alliance_lists(v4_active_new, "Type I: Defense Pact")
    ally_G = create_ally_network(alliance_lists, v4_active_new, weighted=True)
    # DIST
    dist_G = get_dist_G(csvs_root, git_csvs_root)

### %% get communities
# %% LOUVAIN
product_louvain_partition, product_louvain_orig = \
    get_louvain_orig_partition(product_G)
product_louvain_modularity = \
    nx.community.quality.modularity(
        product_G,
        product_louvain_orig)
fig = plot_communities_geo(product_louvain_partition, iso_corr,
                           'Telecommunication equipment', YEAR, show=False)
print('product_louvain_modularity: ', product_louvain_modularity)
fig.update_layout(
    title='Telecommunication equipment communities in 2017 (Louvain)')
fig.show()

# %% GIRVAN NEWMAN
with open('dict_communities_orig.pkl', 'rb') as f:
    dict_communities_orig = pkl.load(f)
product_gn_modularity_best = max(dict_communities_orig.keys())
best_communities_orig = dict_communities_orig[product_gn_modularity_best]
product_gn_partition = dict()
for i, community in enumerate(best_communities_orig):
    for country in community:
        product_gn_partition[country] = i
fig = plot_communities_geo(product_gn_partition, iso_corr,
                           'Telecommunication equipment', YEAR, show=False)
fig.update_layout(
    title='Telecommunication equipment communities in 2017 (Girvan Newman)')
fig.show()

# %% GREEDY
product_greedy_partition, product_greedy_orig = \
    get_greedy_orig_partition(product_G)
product_greedy_modularity = \
    nx.community.quality.modularity(
        product_G,
        product_greedy_orig)
fig = plot_communities_geo(product_greedy_partition, iso_corr,
                           'Telecommunication equipment', YEAR, show=False)
print('product_greedy_modularity: ', product_greedy_modularity)
fig.update_layout(
    title='Telecommunication equipment communities in 2017 (Fastgreedy)')
fig.show()

# %%
# plot three modularities 
fig = px.bar(x=['Girvan Newman(200iters)','Fastgreedy','Louvain'],
       y=[product_gn_modularity_best,
          product_greedy_modularity,
          product_louvain_modularity],
         labels={'x': 'Algorithm', 'y': 'Modularity'},)
fig.update_layout(
    title='Modularity per algorithm')
fig.show()
fig.write_image("images/modularity_per_algo.eps")

louvain_time =0.05050182342529297
greedy_time = 0.2890439033508301
gn_time = 1370.946249961853
time_arr = np.array([gn_time, greedy_time, louvain_time])
time_arr = time_arr/60
fig = px.bar(x=['Girvan Newman(200iters)','Fastgreedy','Louvain'],
             y=time_arr,
             labels={'x': 'Algorithm', 'y': 'Time (m)'},)
fig.update_layout(
    title='Time per algorithm')
fig.show()
fig.write_image("images/time_per_algo.eps")








































if use_igraph:
    # IGRAPH
    # create network from product data for igraph
    # (for walktrap, maybe make weighted, undirected graph later)
    year = 2017
    product_name = '764'
    product_df = products[products['KUSD'] > 0]
    label_columns=['Code_economy', 'Code_partner']

    economy_label = label_columns[0]
    partner_label = label_columns[1]
    filter_product = \
        (product_df['product']==product_name).values
    filter_year = \
        (product_df['year']==year).values 
    product_df_cp = product_df[filter_product & filter_year]\
        [[economy_label, partner_label, 'flow', 'KUSD']].copy()
    # create network
    g = ig.Graph(directed=True)

    economy_nodes = list(product_df_cp[economy_label].unique())
    partner_nodes = list(product_df_cp[partner_label].unique())
    all_nodes = list(set(economy_nodes + partner_nodes))
    g.add_vertices(all_nodes)

    edges = [] 
    weights = []
    for index, row in product_df_cp.iterrows():
        flow = row['flow']
        if flow == 1: # import
            exporter = row[partner_label]
            importer = row[economy_label]
        elif flow == 2: # export
            exporter = row[economy_label]
            importer = row[partner_label]
        kusd = row['KUSD']
        edges.append((exporter, importer))
        weights.append(kusd)

    g.add_edges(edges)
    g.es['weight'] = weights

    # Plot the graph
    layout = g.layout(layout="auto")
    # fig, ax = plt.subplots()
    ig.plot(g)
    # plt.plot(g, layout=layout, vertex_label=g.vs['name'], edge_width=g.es['weight'])
    plt.show()
    breakpoint()

    # %% USING IGRAPH FROM NETWORKX
    ig_product_G = ig.Graph.from_networkx(product_G)
    ig_product_G.vs['name'] = ig_product_G.vs['_nx_name']
    # set weight from networkx graph
    ig_product_G.es['weight'] = [product_G[u][v]['weight'] for u, v in ig_product_G.get_edgelist()]
    # %% get spinglass partition
    algo_product_communities = ig_product_G.community_spinglass()
    # algo_product_communities = ig_product_G.community_walktrap()
    # algo_product_communities = ig_product_G.community_edge_betweenness(clusters=40)

    if isinstance(algo_product_communities, ig.VertexDendrogram):
        algo_product_communities = algo_product_communities.as_clustering()
    # algo_product_communities.membership
    # get partition
    algo_product_partition = dict()
    for i, country in enumerate(ig_product_G.vs['name']):
        algo_product_partition[country] = algo_product_communities.membership[i]

    algo_modularity = algo_product_communities.modularity

    fig = plot_communities_geo(algo_product_partition, iso_corr,
                            'Telecommunication equipment', YEAR)
    fig.show()

    print(f'louvain:',product_louvain_modularity)
    print(f'spinglass:',algo_modularity)
    print(f'spinglass > louvain:',algo_modularity > product_louvain_modularity)
