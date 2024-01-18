# %%
# imports
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px

import networkx as nx
# import geopandas as gpd
from geopy.distance import geodesic
from sklearn.metrics import normalized_mutual_info_score as NMI

import pickle as pkl
from warnings import filterwarnings
filterwarnings('ignore')

from thefuzz import fuzz
from hfuncs.preprocessing import *
from hfuncs.plotting import *
from hfuncs.graphs import *
from hfuncs.plotting_communities import *
from hfuncs.rta import *
from hfuncs.dist import *
from hfuncs.alliance import *

# %%
# for loading data
csvs_root= '../../csvs/'
git_csvs_root = '../../csvs_git/'
data_root= '../../../../data/trade/BACI/'
data_file_name='top_ex_imp_2017_21_new.csv'
# YEAR = 2019

# %%
# load and preprocess PRODUCT data
products, country_df = preprocess_products(
    exports=False,
    imports=True,
    csvs_root=csvs_root,
    data_root=data_root,
    data_file_name=data_file_name,)
products = products.dropna(subset=['Code_economy', 'Code_partner']) # limit to countries
products = products[products['partner_label'] != products['economy_label']]

NMI_list = []
for YEAR in (2017, 2018, 2019):
    print(YEAR)
# %%
# load and preprocess RTA data
# load and preprocess RTA data
    rta = pd.read_csv(csvs_root + 'AllRTAs_new.csv')
    tmp_rta = preprocess_rta(rta)

# for converting RTA/ABBVs to countries
    EU_countries_str = 'Austria; Belgium; Cyprus; Czech Republic; Denmark; Estonia; Finland; France; Germany; Greece; Hungary; Ireland; Italy; Latvia; Lithuania; Luxembourg; Malta; Netherlands; Poland; Portugal; Slovak Republic; Slovenia; Spain; Sweden; United Kingdom'
    abbv_RTA_ids = [1170, 7, 130, 151, 909, 152, 17]
    abbv_rta_dict = abbv_to_countries_dict(tmp_rta, EU_countries_str, abbv_RTA_ids)

# convert RTA/ABVVs to countries
    tmp_rta_new = abbv_to_countries(tmp_rta, abbv_rta_dict)
    tmp_rta_new.reset_index(inplace=True, drop=True)

    rta_year = get_rta_year(tmp_rta_new, str(YEAR), git_csvs_root)

# get all RTAs in country codes
    rta_to_country_codes = pd.read_csv(git_csvs_root + 'rta_to_country_codes.csv')
    rta_country_codes_year, country_codes_per_rta_year = \
        get_country_codes_per_RTA(rta_year, rta_to_country_codes)
    rta_year_G = create_rta_network(rta_country_codes_year, country_codes_per_rta_year)
    rta_year_partition = get_louvain_partition(rta_year_G)

# create product network
    product_G = create_network(
        YEAR,
        '764',
        products,
        ['Code_economy', 'Code_partner']
    )
    # total_G = create_network(
    #     YEAR,
    #     'TOTAL',
    #     products,
    #     ['Code_economy', 'Code_partner']
    # )
# %%
# get product communities, partition
    product_communities = nx.community.louvain_communities(product_G)
    product_communities = list(product_communities)
    product_partition = dict()
    for i, community in enumerate(product_communities):
        for country in community:
            product_partition[country] = i
    product_communities_set = set(product_partition.values())

# %%
# get and preprocess DIST data
    geos = pd.read_csv(csvs_root + 'geo_cepii.csv', keep_default_na=False)
# %%
# get distance between countries
# %% 
    dist_inv = get_dist_inv(geos)
    dist_G = get_dist_network(dist_inv)
# get distance communities, partition
    dist_communities = \
        nx.community.louvain_communities(dist_G)
    dist_communities = list(dist_communities)
    dist_partition = dict()
    for i, community in enumerate(dist_communities):
        for country in community:
            dist_partition[country] = i
    dist_communities_set = set(dist_partition.values())

# %%
# load ALLIANCE data
    v4 = pd.read_csv(csvs_root + 'version41_csv/alliance_v41_by_member.csv')
    v4_to_products = pd.read_csv(git_csvs_root + 'v4_to_products.csv')
    v4_active_new = preprocess_alliances(v4, v4_to_products)
    alliance_lists = get_alliance_lists(v4_active_new)
    ally_G = create_ally_network(alliance_lists, v4_active_new)
# %% 
# get alliance communmities
    alliance_communities = nx.community.louvain_communities(ally_G)
    alliance_communities = list(alliance_communities)
    alliance_communities
# %%
    alliance_partition = dict()
    for i, community in enumerate(alliance_communities):
        for country in community:
            alliance_partition[country] = i
    alliance_communities_set = set(alliance_partition.values())

    # plot_basic_communities(ally_G, alliance_partition)

# %%
# normalize each partitions
    all_countries = list(product_G.nodes())
    all_common_countries = []
    for country in all_countries:
        if country not in rta_year_partition.keys():
            print(country, 'not in rta_year_partition')
            pass
        elif country not in product_partition.keys():
            print(country, 'not in product_partition')
            pass
        elif country not in alliance_partition.keys():
            print(country, 'not in alliance_partition')
            pass
        elif country not in dist_partition.keys():
            print(country, 'not in dist_partition')
            pass
        else:
            all_common_countries.append(country)
# normalize rta_year_partition
    rta_year_partition_normalized = dict()
    for country in all_common_countries:
        rta_year_partition_normalized[country] = rta_year_partition[country]
# normalize product_partition
    product_partition_normalized = dict()
    for country in all_common_countries:
        product_partition_normalized[country] = product_partition[country]
# normalize dist_partition
    dist_partition_normalized = dict()
    for country in all_common_countries:
        dist_partition_normalized[country] = dist_partition[country]
# # normalize alliance_partition
    alliance_partition_normalized = dict()
    for country in all_common_countries:
        alliance_partition_normalized[country] = alliance_partition[country]

# %%
# compute NMI
    product_partition_normalized_values = list(product_partition_normalized.values())
    rta_year_partition_normalized_values = list(rta_year_partition_normalized.values())
    dist_partition_normalized_values = list(dist_partition_normalized.values())
    alliance_partition_normalized_values = list(alliance_partition_normalized.values())

    product_v_rta = NMI(product_partition_normalized_values, rta_year_partition_normalized_values)
    product_v_dist = NMI(product_partition_normalized_values, dist_partition_normalized_values)
    product_v_alliance = NMI(product_partition_normalized_values, alliance_partition_normalized_values)
    print(f'NMI(product, rta) = {product_v_rta}')
    print(f'NMI(product, dist) = {product_v_dist}')
    print(f'NMI(product, alliance) = {product_v_alliance}')
    NMI_list.append([product_v_rta, product_v_dist, product_v_alliance])

breakpoint()
# %%
# what are the friends of a country in each network?
# country = 'US'
country = False
if country:
    dist_country_community = dist_partition[country]
    dist_country_friends = \
        [code for code in dist_partition.keys() if \
            dist_partition[code] == dist_country_community]
    rta_country_community = rta_year_partition[country]
    rta_country_friends = \
        [code for code in rta_year_partition.keys() if \
            rta_year_partition[code] == rta_country_community]
    product_country_community = product_partition[country]
    product_country_friends = \
        [code for code in product_partition.keys() if \
            product_partition[code] == product_country_community]
    print(f'{country} product friends: {product_country_friends}')
    print(f'{country} rta friends: {rta_country_friends}')
    print(f'{country} dist friends: {dist_country_friends}')

