# %%
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

import pickle as pkl
from warnings import filterwarnings
filterwarnings('ignore')

from thefuzz import fuzz

from hfuncs.preprocessing import *
from hfuncs.plotting import *
from hfuncs.graphs import *
from hfuncs.plotting_communities import *

# %%
# # load data
csvs_root= '../../csvs/'
git_csvs_root = '../../csvs_git/'
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
country_df = pd.read_csv(data_root + 'countries.csv')
# %%
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
del(products_economy_labeled)
del(products_labeled)
# %%
products = products.dropna(subset=['Code_economy', 'Code_partner']) # limit to countries
products = products[products['partner_label'] != products['economy_label']]

# %% [markdown]
# # RTA
# %%
rta = pd.read_csv(csvs_root + 'AllRTAs_new.csv')

# %% [markdown]
# ## functions for RTA
# %%
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

# %% [markdown]
# ## RTAのデータを整形
rta['date_of_sign_G'] = \
    pd.to_datetime(rta['Date of Signature (G)'], format='%d-%b-%y', errors='coerce')
rta['date_of_sign_S'] = \
    pd.to_datetime(rta['Date of Signature (S)'], format='%d-%b-%y', errors='coerce')
rta['inactive_date'] = \
    pd.to_datetime(rta['Inactive Date'], format='%d-%b-%y', errors='coerce')
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
use_filter = post_2019_add_filter | currently_active_filter

tmp_rta = rta[use_filter]
tmp_rta = tmp_rta[['RTA ID', 'RTA Name', 'Status', 'date_of_sign_G',
           'inactive_date', 'Original signatories', 'Current signatories',
           'Specific Entry/Exit dates', 'Coverage', 'Type']]

# %% [markdown]
# ## work on 2016, 2017, 2018 RTA network considering enties/exits
has_exits_post_2016_filter = \
    (tmp_rta['Specific Entry/Exit dates'].notna()).values
changed_in_range = tmp_rta[has_exits_post_2016_filter]['Specific Entry/Exit dates']\
    .apply(lambda x: has_years_in_string(x))
tmp_rta[has_exits_post_2016_filter][changed_in_range.values].shape

# %%
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

# %%
# replace all the strings in tmp_dict with country codes
def replace_with_country(string, rta_dict):
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
            apply(replace_with_country, args=(abbv_rta_dict,))
    return tmp_rta_new
# %%
replace_abbv = False
EU_countries_str = 'Austria; Belgium; Cyprus; Czech Republic; Denmark; Estonia; Finland; France; Germany; Greece; Hungary; Ireland; Italy; Latvia; Lithuania; Luxembourg; Malta; Netherlands; Poland; Portugal; Slovak Republic; Slovenia; Spain; Sweden; United Kingdom'
if replace_abbv:
    tmp_rta_new = replace_abbvs_with_countries(tmp_rta)
elif not replace_abbv:
    tmp_rta_new = tmp_rta.copy()
# %%
len(list(EU_countries_str.split(';')))

# %%
# split the string and map to country codes
rta_to_country_codes = pd.read_csv(git_csvs_root + 'rta_to_country_codes.csv')

country_codes_per_RTA = []
all_RTA_ids = tmp_rta_new['RTA ID'].unique()
rta_country_codes = set()
for RTA_id in all_RTA_ids:
    tmp_str = tmp_rta_new[tmp_rta_new['RTA ID'] == RTA_id]['Current signatories'].values[0]
    if tmp_str is np.nan:
        print('No Current signatories')
        continue
    else:
        tmp_str_new = [x.strip() for x in tmp_str.split(';')]
        tmp_df = pd.DataFrame(tmp_str_new, columns=['country']).merge(
            rta_to_country_codes,
            left_on='country',
            right_on='RTA_country',
            how='left')
        # ↓remove RTA countries that didn't match with country codes
        # tmp_df = tmp_df.dropna(subset=['Code_economy']) 
        tmp_df_codes = tmp_df['Code_economy'].values.tolist()
        country_codes_per_RTA.append(tmp_df_codes)
        rta_country_codes = rta_country_codes.union(set(tmp_df_codes))
# np.array(country_codes_per_RTA).shape
# rta_country_codes

# %% create RTA network
G = nx.Graph()
economy_nodes = rta_country_codes
G.add_nodes_from(economy_nodes)
edges_set = []
for code_list in country_codes_per_RTA:
    for i in range(len(code_list)):
        for j in range(i+1, len(code_list)):
            if set((code_list[i], code_list[j])) in edges_set:
                print(code_list[i], code_list[j])
                continue
            else:
                G.add_edge(code_list[i], code_list[j])
                edges_set.append(set((code_list[i], code_list[j])))

# %% get partition
communities = \
    nx.community.louvain_communities(G)
communities = list(communities)
partition = dict()
for i, community in enumerate(communities):
    for country in community:
        partition[country] = i
communities = set(partition.values())

# %% get position
position = nx.spring_layout(G, k=0.9, iterations=50)

# %% plot
figsize = (14, 14)
fig, ax = plt.subplots(figsize=figsize)
# position = nx.circular_layout(sub_G, scale=2.5)
cmap = plt.get_cmap('Set1')
communities = set(partition.values())
colors = \
    [cmap(i) for i in np.linspace(0.2, 0.7, len(communities))]
for i, community in enumerate(communities):
    nodes = [node for node in G.nodes() if partition[node]==community]
    print(nodes)
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

# %% [markdown]

# %% [markdown]
# 2016-2019の間にinactiveになったRTAは、
# id: 502, Turkiye-Jordan FTAのみ
# よってこれ以外のRTA(inactive post 2019) を加えたRTA郡を対象にする
# %%

# %% [markdown]
# # ASEAN(AFTA) ID : 1170
# find_fuzz(tmp_rta, 'ASEAN Free Trade Area')
# # SACU ID : 7
# find_fuzz(tmp_rta, 'Southern African Customs Union')
# # Southern Common Market ID : 130
# find_fuzz(tmp_rta, 'Southern Common Market')
# # Central American Common Market ID : 151
# find_fuzz(tmp_rta, 'Central American Common Market')
# # Eurasian Economic Union ID : 909
# find_fuzz(tmp_rta, 'Eurasian Economic Union')
# # European Free Trade Association ID : 152
# find_fuzz(tmp_rta, 'European Free Trade Association')
# # Gulf Cooperation Council ID : 17
# find_fuzz(tmp_rta, 'Gulf Cooperation Council')
# # European Union ID : NONE
# # EU pre 2020:

# %%
# DON'T WRTITE TO CSV ANYMORE
# INSTEAD, READ
# rta_countries = pd.read_csv(git_csvs_root + 'tmp_rta_countries.csv')
# %%
# # write rta countries to csv file
# countries = set()
# for index, row in tmp_rta.iterrows():
#     if row['Current signatories'] is np.nan:
#         lis = row['Original signatories'].split(';')
#         lis = [x.strip() for x in lis]
#         countries = countries.union(set(lis))
#         continue
#     else:
#         lis = row['Current signatories'].split(';')
#         lis = [x.strip() for x in lis]
#         countries = countries.union(set(lis))
# countries_df = pd.DataFrame(list(countries), columns=['RTA_country'])
# tmp_country_codes = products[['economy_label', 'Code_economy']].drop_duplicates()

# countries_df = countries_df.merge(
#     tmp_country_codes,
#     left_on='RTA_country',
#     right_on='economy_label',
#     how='outer'
# )
# countries_df.sort_values(by='RTA_country', inplace=True)
# # countries_df.to_csv(csvs_root + 'tmp_rta_countries_old.csv', index=False)
# countries_df.head()

