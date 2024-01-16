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

# %%
# stuff regarding running the script
plot_rta = True
# %%
# for loading data
csvs_root= '../../csvs/'
git_csvs_root = '../../csvs_git/'
data_root= '../../../../data/trade/BACI/'
data_file_name='top_ex_imp_2017_21_new.csv'

# %%
# funtions for RTA
def minus_100y(date):
    if date.year > 2023:
        return date - pd.offsets.DateOffset(years=100)
    else:
        return date
def has_years_in_string(string):
    if string is np.nan:
        return string
    elif '2016' in string or '2017' in string or '2018' in string or '2019' in string:
        return True
    else:
        return False
def find_fuzz(rta_df, country, column='RTA Name'):
    fuzz_scores = rta_df[column].apply(lambda x: fuzz.partial_ratio(x, country))
    return rta_df[fuzz_scores > 80]

# REPLACE ABBREVIATIONS WITH COUNTRIES
def abbv_to_countries_dict(
        EU_countries_str = 'Austria; Belgium; Cyprus; Czech Republic; Denmark; Estonia; Finland; France; Germany; Greece; Hungary; Ireland; Italy; Latvia; Lithuania; Luxembourg; Malta; Netherlands; Poland; Portugal; Slovak Republic; Slovenia; Spain; Sweden; United Kingdom',
        abbv_RTA_ids=[1170, 7, 130, 151, 909, 152, 17]
    ):
    abbv_rta_dict = {}
    for rta_id in abbv_RTA_ids:
        rta_name = \
            tmp_rta[tmp_rta['RTA ID'] == rta_id]['RTA Name'].values[0]
        countries_str = \
            tmp_rta[tmp_rta['RTA ID'] == rta_id]['Current signatories'].values[0]
        abbv_rta_dict[rta_name] = countries_str
    abbv_rta_dict['European Union'] = EU_countries_str
    return abbv_rta_dict
def replace_abbv_with_country(string, rta_dict):
    if string is np.nan:
        return string
    for key, value in rta_dict.items():
        string = string.replace(key, value)
    return string
        
def replace_abbvs_with_countries(
        tmp_rta,
        EU_countries_str = 'Austria; Belgium; Cyprus; Czech Republic; Denmark; Estonia; Finland; France; Germany; Greece; Hungary; Ireland; Italy; Latvia; Lithuania; Luxembourg; Malta; Netherlands; Poland; Portugal; Slovak Republic; Slovenia; Spain; Sweden; United Kingdom',
        abbv_RTA_ids = [1170, 7, 130, 151, 909, 152, 17]
    ):
    abbv_rta_dict = abbv_to_countries_dict(EU_countries_str, abbv_RTA_ids)
    tmp_rta_new = tmp_rta.copy()
    tmp_rta_new['Current signatories'] = tmp_rta['Current signatories'].\
        apply(lambda string: replace_abbv_with_country(string, abbv_rta_dict))
    # breakpoint()
    return tmp_rta_new

# %% [markdown]
# ## RTAのデータを整形
def preprocess_rta(rta):
    rta['date_of_sign_G'] = \
        pd.to_datetime(rta['Date of Signature (G)'], format='%d-%b-%y', errors='coerce')
    rta['date_of_sign_S'] = \
        pd.to_datetime(rta['Date of Signature (S)'], format='%d-%b-%y', errors='coerce')
    rta['inactive_date'] = \
        pd.to_datetime(rta['Inactive Date'], format='%d-%b-%y', errors='coerce')
    rta['date_of_entry_into_force_G'] = \
        pd.to_datetime(rta['Date of Entry into Force (G)'], format='%d-%b-%y', errors='coerce')
    rta['date_of_sign_G'] = rta['date_of_sign_G'].apply(lambda x: minus_100y(x))
    rta['date_of_sign_S'] = rta['date_of_sign_S'].apply(lambda x: minus_100y(x))
    rta['inactive_date'] = rta['inactive_date'].apply(lambda x: minus_100y(x))

    sign_pre_2016_filter = (rta['date_of_sign_G'] < pd.to_datetime('2016-01-01')).values

    inactive_between_2016_2019_filter = \
        (rta['inactive_date'] > pd.to_datetime('2016-01-01')).values & \
        (rta['inactive_date'] < pd.to_datetime('2020-01-01')).values # 2016-19の間にinactive
    inactive_post_2019_filter = \
        (rta['inactive_date'] >= pd.to_datetime('2020-01-01')).values # 2016年以降にinactive
    post_2019_add_filter = \
        inactive_post_2019_filter & ~inactive_between_2016_2019_filter

    currently_active_filter = (rta['Status'] == 'In Force').values
    use_filter = (post_2019_add_filter | currently_active_filter) & sign_pre_2016_filter

    tmp_rta = rta[use_filter]
    tmp_rta = tmp_rta[['RTA ID', 'RTA Name', 'Status', 'date_of_sign_G',
               'inactive_date', 'Original signatories', 'Current signatories',
               'Specific Entry/Exit dates', 'Coverage', 'Type']]
    return tmp_rta

# %%
# load and preprocess RTA data
rta = pd.read_csv(csvs_root + 'AllRTAs_new.csv')
tmp_rta = preprocess_rta(rta)
# %%
# for converting RTA/ABBVs to countries
EU_countries_str = 'Austria; Belgium; Cyprus; Czech Republic; Denmark; Estonia; Finland; France; Germany; Greece; Hungary; Ireland; Italy; Latvia; Lithuania; Luxembourg; Malta; Netherlands; Poland; Portugal; Slovak Republic; Slovenia; Spain; Sweden; United Kingdom'
abbv_RTA_ids = [1170, 7, 130, 151, 909, 152, 17]
abbv_rta_dict = abbv_to_countries_dict(EU_countries_str, abbv_RTA_ids)
# %%
# convert RTA/ABVVs to countries
tmp_rta_new = tmp_rta.copy()
tmp_rta_new['Current signatories'] = tmp_rta['Current signatories'].\
    apply(lambda string: replace_abbv_with_country(string, abbv_rta_dict))
tmp_rta_new = replace_abbvs_with_countries(tmp_rta)
# %%
# get all RTAs in country codes
rta_to_country_codes = pd.read_csv(git_csvs_root + 'rta_to_country_codes.csv')
country_codes_per_RTA = []
all_RTA_ids = tmp_rta_new['RTA ID'].unique()
rta_country_codes = set()
# after adding abbvs
for RTA_id in all_RTA_ids:
    tmp_row = tmp_rta_new[tmp_rta_new['RTA ID'] == RTA_id]
    tmp_str = tmp_row['Current signatories'].values[0]
    if tmp_str is np.nan: # only exception is NAFTA
        print('No Current signatories for:', tmp_row['RTA Name'])
        continue
    else:
        tmp_str_new = [x.strip() for x in tmp_str.split(';')]
        tmp_df = pd.DataFrame(tmp_str_new, columns=['country']).merge(
            rta_to_country_codes,
            left_on='country',
            right_on='RTA_country',
            how='left')
        # ↓remove RTA countries that didn't match with country codes
        tmp_df = tmp_df.dropna(subset=['Code_economy']) 
        tmp_df_codes = tmp_df['Code_economy'].values.tolist()
        country_codes_per_RTA.append(tmp_df_codes)
        rta_country_codes = rta_country_codes.union(set(tmp_df_codes))
# %% 
# create RTA network
# 1/12TODOS:
    # 1. 2016-19末 の間にin-forceになったRTAを考慮する 
        # 30個くらいある
G_rta = nx.Graph()
economy_nodes = rta_country_codes
G_rta.add_nodes_from(economy_nodes)
edges_set = []
for code_list in country_codes_per_RTA:
    for i in range(len(code_list)):
        for j in range(i+1, len(code_list)):
            if set((code_list[i], code_list[j])) in edges_set:
                continue
            else: # add edge
                G_rta.add_edge(code_list[i], code_list[j])
                edges_set.append(set((code_list[i], code_list[j])))
# %% 
# get rta communities, partition
rta_communities = \
    nx.community.louvain_communities(G_rta)
rta_communities = list(rta_communities)
rta_partition = dict()
for i, community in enumerate(rta_communities):
    for country in community:
        rta_partition[country] = i
rta_communities = set(rta_partition.values())
# %%
# plot RTA network
partition = rta_partition
G = G_rta
figsize = (8, 8)

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
if plot_rta:
    plt.show()

# %%
# %%
# load and preprocess product data
def preprocess_products(
        exports=True,
        imports=True,
        csvs_root=csvs_root,
        data_root=data_root,
        data_file_name=data_file_name,
        ):
    products = get_product_data(
        exports=exports,
        imports=imports,
        csvs_root=csvs_root,
        data_root=data_root,
        data_file_name=data_file_name,
    )
    countries = get_countries(data_root=data_root)
    country_df = pd.read_csv(data_root + 'countries.csv')
    products_economy_labeled = products.merge(
        country_df,
        left_on='economy_label',
        right_on='Name',
        how='left')
    products_labeled = products_economy_labeled.merge(
        country_df,
        left_on='partner_label',
        right_on='Name',
        how='left',
        suffixes=('_economy', '_partner'))
    products = products_labeled.copy()
    return products, country_df
products, country_df = preprocess_products(
    exports=True,
    imports=True,
    csvs_root=csvs_root,
    data_root=data_root,
    data_file_name=data_file_name,)
products = products.dropna(subset=['Code_economy', 'Code_partner']) # limit to countries
products = products[products['partner_label'] != products['economy_label']]
# create product network
product_G = create_network(
    2019,
    '764',
    products,
    ['Code_economy', 'Code_partner']
)
# %%
# get product communities, partition
product_communities = nx.community.louvain_communities(product_G)
product_communities = list(product_communities)
product_partition = dict()
for i, community in enumerate(product_communities):
    for country in community:
        product_partition[country] = i
product_communities = set(product_partition.values())
# %%
# get countries in product network
all_countries = list(product_G.nodes())
# %%
# get and preprocess dist data
geos = pd.read_csv(csvs_root + 'geo_cepii.csv', keep_default_na=False)
# %%
# get distance between countries
dist_df = pd.DataFrame(columns=['economy', 'partner', 'dist'])
exclude_sets = []
for economy in geos.iso2:
    for partner in geos.iso2:
        if economy == partner or set([economy, partner]) in exclude_sets:
            continue
        exclude_sets.append(set([economy, partner]))
        dist = geodesic(
            geos[geos.iso2==economy][['lat', 'lon']].values[0],
            geos[geos.iso2==partner][['lat', 'lon']].values[0]
        ).km
        dist_df = dist_df.append(
            {
                'economy': economy,
                'partner': partner,
                'dist': dist
            },
            ignore_index=True
        )
# %%
# inverting distance
dist_df_inv = dist_df.copy()
dist_df_inv['dist_inv'] = dist_df_inv['dist'].apply(lambda x: 1/x)
# %%
# create distance network
dist_G = nx.Graph()
economy_nodes = list(dist_df_inv['economy'].unique())
partner_nodes = list(dist_df_inv['partner'].unique())
dist_G.add_nodes_from(economy_nodes, node_type='export')
dist_G.add_nodes_from(partner_nodes, node_type='import')
for index, row in dist_df_inv.iterrows():
    exporter = row['economy']
    importer = row['partner']
    dist_inv = row['dist_inv']
    dist_G.add_edge(exporter, importer, weight=dist_inv)
# %%
# get distance communities, partition
dist_communities = \
    nx.community.louvain_communities(dist_G)
dist_communities = list(dist_communities)
dist_partition = dict()
for i, community in enumerate(dist_communities):
    for country in community:
        dist_partition[country] = i
dist_communities = set(dist_partition.values())

# %%
# normalize rta_partition
rta_partition_normalized = dict()
for country in all_countries:
    try:
        rta_partition_normalized[country] = rta_partition[country]
    except KeyError:
        rta_partition_normalized[country] = -1
# %%
# normalize dist_partition
dist_partition_normalized = dict()
for country in all_countries:
    try:
        dist_partition_normalized[country] = dist_partition[country]
    except KeyError:
        dist_partition_normalized[country] = -2

# %%
# compute NMI
product_partition_values = list(product_partition.values())
rta_partition_normalized_values = list(rta_partition_normalized.values())
dist_partition_normalized_values = list(dist_partition_normalized.values())
product_v_rta = NMI(product_partition_values, rta_partition_normalized_values)
product_v_dist = NMI(product_partition_values, dist_partition_normalized_values)
print(f'NMI(product, rta) = {product_v_rta}')
print(f'NMI(product, dist) = {product_v_dist}')

# %%
# what are the friends of a country in each network?
country = 'US'
country = False
if country:
    dist_country_community = dist_partition[country]
    dist_country_friends = \
        [code for code in dist_partition.keys() if \
            dist_partition[code] == dist_country_community]
    rta_country_community = rta_partition[country]
    rta_country_friends = \
        [code for code in rta_partition.keys() if \
            rta_partition[code] == rta_country_community]
    product_country_community = product_partition[country]
    product_country_friends = \
        [code for code in product_partition.keys() if \
            product_partition[code] == product_country_community]
    print(f'{country} product friends: {product_country_friends}')
    print(f'{country} rta friends: {rta_country_friends}')
    print(f'{country} dist friends: {dist_country_friends}')

