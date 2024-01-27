# %%
import pandas as pd
import plotly.express as px
from sklearn.metrics import normalized_mutual_info_score as NMI
import igraph as ig
import pickle as pkl
import itertools

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

# %% stuff to run every year
# PRODUCT
product_G = create_network(
    YEAR,
    '764',
    products,
    ['Code_economy', 'Code_partner'])
total_G = create_network(
    YEAR,
    'TOTAL',
    products[products['KUSD'] > 0],
    ['Code_economy', 'Code_partner'])
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

# %% get louvain partitions
def get_louvain_orig_partition(G):
    communities_orig = nx.community.louvain_communities(G)
    communities = list(communities_orig)
    partition = dict()
    for i, community in enumerate(communities):
        for country in community:
            partition[country] = i
    return partition, communities_orig
def get_gn_orig_partition(G):
    communities_orig = nx.community.girvan_newman(G)
    communities_orig_normalized = []
    tmp_communities_orig = next(communities_orig)
    for community in tmp_communities_orig:
        print('gn')
        communities_orig_normalized.append(community)
    communities = list(communities_orig)
    partition = dict()
    for i, community in enumerate(communities):
        for country in community:
            partition[country] = i
    return partition, communities_orig_normalized
# %% DEBUG GN
G = product_G.copy()
communities_orig = nx.community.girvan_newman(G)
communities_orig_normalized = []
# tmp_communities_orig = next(communities_orig)
max_iter = 200
old_mod = -1
modularities = []
for i, tmp_communities_orig in enumerate(communities_orig):
    if i > max_iter:
        break
    else:
        print(i, end=' ')
        modularities.append(new_mod)
        communities_orig_normalized.append(tmp_communities_orig)
        new_mod = nx.community.quality.modularity(
            G, tmp_communities_orig)
        if new_mod > old_mod:
            print(f'new modularity for gn: {new_mod}')
            old_mod = new_mod
            communities_orig = tmp_communities_orig



# %%
communities_orig_normalized = []
for community in tmp_communities_orig:
    print('gn')
    communities_orig_normalized.append(community)
communities = list(communities_orig)
partition = dict()
for i, community in enumerate(communities):
    for country in community:
        partition[country] = i
fig = plot_communities_geo(partition, iso_corr,
                            'Telecommunication equipment', YEAR)
fig.show()
# %%

louvain_product_partition, louvain_product_orig = get_louvain_orig_partition(product_G)
gn_product_partition, gn_product_orig = get_gn_orig_partition(product_G)
fig = plot_communities_geo(louvain_product_partition, iso_corr,
                           'Telecommunication equipment', YEAR)
fig.show()
fig = plot_communities_geo(gn_product_partition, iso_corr,
                           'Telecommunication equipment', YEAR)
fig.show()
breakpoint()

# using igraph
ig_product_G = ig.Graph.from_networkx(product_G)
ig_product_G.vs['name'] = ig_product_G.vs['_nx_name']

# %% get spinglass partition
# sg_product_communities = ig_product_G.community_spinglass()
sg_product_communities = ig_product_G.community_walktrap()
# sg_product_communities = ig_product_G.community_edge_betweenness(clusters=40)
if isinstance(sg_product_communities, ig.VertexDendrogram):
    sg_product_communities = sg_product_communities.as_clustering()
# %%
sg_product_communities.membership
print(type(sg_product_communities))
# get partition
sg_product_partition = dict()
for i, country in enumerate(ig_product_G.vs['name']):
    sg_product_partition[country] = sg_product_communities.membership[i]
fig = plot_communities_geo(sg_product_partition, iso_corr,
                           'Telecommunication equipment', YEAR)
fig.show()
product_modularity = \
    nx.community.quality.modularity(
        product_G,
        louvain_product_orig)
sg_modularity = sg_product_communities.modularity
print(f'louvain:',product_modularity)
print(f'spinglass:',sg_modularity)
print(f'spinglass > louvain:',sg_modularity > product_modularity)


# # %%
# ig_total_G = ig.Graph.from_networkx(total_G)
# ig_rta_year_G = ig.Graph.from_networkx(rta_year_G)
# ig_alliance_G = ig.Graph.from_networkx(ally_G)
# ig_dist_G = ig.Graph.from_networkx(dist_G)

# # %%
# total_partition, total_partition_orig = get_louvain_orig_partition(total_G)
# rta_year_partition, rta_partition_orig = get_louvain_orig_partition(rta_year_G)
# alliance_partition, alliance_partition_orig = get_louvain_orig_partition(ally_G)
# for i, country in enumerate(non_allied_countries):
#     alliance_partition[country] = -i
#     alliance_partition_orig.append({country})
# dist_partition, dist_partition_orig  = get_louvain_orig_partition(dist_G)

# %%
