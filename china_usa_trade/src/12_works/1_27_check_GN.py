# %%
import pandas as pd
import plotly.express as px
from sklearn.metrics import normalized_mutual_info_score as NMI
import igraph as ig
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
run_GN = False

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
if run_GN:
    G = product_G.copy()
    communities_orig = nx.community.girvan_newman(G)
    dict_communities_orig = {}
    # tmp_communities_orig = next(communities_orig)
    max_iter = 200
    new_mod = -1
    modularities = []
    start_time = time.time()
    for i, tmp_communities_orig in enumerate(communities_orig):
        if i > max_iter:
            break
        elif new_mod > 0.18:
            break
        else:
            if i%10 == 0:
                print(i, end=' ')
            tmp_mod = nx.community.quality.modularity(
                G, tmp_communities_orig)
            modularities.append(tmp_mod)
            if tmp_mod > new_mod:
                print(f'new modularity for gn: {tmp_mod}')
                new_mod = tmp_mod
                dict_communities_orig.update({new_mod:tmp_communities_orig})
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'elapsed time: {elapsed_time} seconds')
    with open('dict_communities_orig_2.pkl', 'wb') as f:
        pkl.dump(dict_communities_orig, f)
    with open('modularities_2.pkl', 'wb') as f:
        pkl.dump(modularities, f)

# %% plot communities
with open('dict_communities_orig.pkl', 'rb') as f:
    dict_communities_orig = pkl.load(f)
best_mod = max(dict_communities_orig.keys())
best_communities_orig = dict_communities_orig[best_mod]
product_gn_partition = dict()
for i, community in enumerate(best_communities_orig):
    for country in community:
        product_gn_partition[country] = i
fig = plot_communities_geo(product_gn_partition, iso_corr, show=True)
# fig.write_image('images/product_gn_partition.eps')

# %% plot modularities
with open('modularities.pkl', 'rb') as f:
    modularities = pkl.load(f)
fig = px.line(
    x=range(len(modularities)),
    y=modularities,
    title='Modularity score of Girvan Newman algorithm')
fig.update_layout(
    xaxis_title='Iteration',
    yaxis_title='Modularity')
fig.show()

fig.write_image('images/modularities.eps')







