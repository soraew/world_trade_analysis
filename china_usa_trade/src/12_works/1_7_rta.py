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

# %%
rta = pd.read_csv(csvs_root + 'AllRTAs_new.csv')

# %% [markdown]
# ## convert date columns in RTA to datetime
# %%
rta['date_of_sign_G'] = \
    pd.to_datetime(rta['Date of Signature (G)'], format='%d-%b-%y', errors='coerce')
rta['date_of_sign_S'] = \
    pd.to_datetime(rta['Date of Signature (S)'], format='%d-%b-%y', errors='coerce')
rta['inactive_date'] = \
    pd.to_datetime(rta['Inactive Date'], format='%d-%b-%y', errors='coerce')

def minus_100y(date):
    if date.year > 2023:
        return date - pd.offsets.DateOffset(years=100)
    else:
        return date

rta['date_of_sign_G'] = rta['date_of_sign_G'].apply(lambda x: minus_100y(x))
rta['date_of_sign_S'] = rta['date_of_sign_S'].apply(lambda x: minus_100y(x))
rta['inactive_date'] = rta['inactive_date'].apply(lambda x: minus_100y(x))

sign_pre_2016_filter = (rta['date_of_sign_G'] < pd.to_datetime('2016-01-01')).values
# %% [markdown]
# 2016-2019の間にinactiveになったRTAは、
# id: 502, Turkiye-Jordan FTAのみ
# よってこれ以外のRTA(inactive post 2019) を加えたRTA郡を対象にする
# %%
inactive_between_2016_2019_filter = \
    (rta['inactive_date'] > pd.to_datetime('2016-01-01')).values & \
    (rta['inactive_date'] < pd.to_datetime('2020-01-01')).values # 2016-19の間にinactive
inactive_post_2019_filter = \
    (rta['inactive_date'] >= pd.to_datetime('2020-01-01')).values # 2016年以降にinactive

post_2019_add_filter = ~inactive_between_2016_2019_filter & inactive_post_2019_filter

currently_active_filter = (rta['Status'] == 'In Force').values
use_filter = post_2019_add_filter | currently_active_filter

tmp_rta = rta[use_filter]
tmp_rta = tmp_rta[['RTA ID', 'RTA Name', 'Status', 'date_of_sign_G', 'inactive_date',
           'Original signatories', 'Current signatories', 'Specific Entry/Exit dates', 'Coverage',
           'Type'
           ]]
has_exits_post_2016_filter = (tmp_rta['Specific Entry/Exit dates'].notna()).values
def has_years_in_string(string):
    if string is np.nan:
        return string
    elif '2016' in string or '2017' in string or '2018' in string or '2019' in string:
        return True
    else:
        return False

changed_in_range = tmp_rta[has_exits_post_2016_filter]['Specific Entry/Exit dates']\
    .apply(lambda x: has_years_in_string(x))
tmp_rta[has_exits_post_2016_filter][changed_in_range.values].shape

# %%
# write rta countries to csv file
countries = set()
for index, row in tmp_rta.iterrows():
    if row['Current signatories'] is np.nan:
        lis = row['Original signatories'].split(';')
        lis = [x.strip() for x in lis]
        countries = countries.union(set(lis))
        continue
    else:
        lis = row['Current signatories'].split(';')
        lis = [x.strip() for x in lis]
        countries = countries.union(set(lis))
countries_df = pd.DataFrame(list(countries), columns=['RTA_country'])
tmp_country_codes = products[['economy_label', 'Code_economy']].drop_duplicates()

countries_df = countries_df.merge(
    tmp_country_codes,
    left_on='RTA_country',
    right_on='economy_label',
    how='outer'
)
countries_df.sort_values(by='RTA_country', inplace=True)
countries_df.to_csv(csvs_root + 'tmp_rta_countries.csv', index=False)
countries_df

# %%
# あぶれているものをfuzzで検索
def find_fuzz(rta_df, country, column='RTA Name'):
    fuzz_scores = rta_df[column].apply(lambda x: fuzz.partial_ratio(x, country))
    return rta_df[fuzz_scores > 80]
# ASEAN(AFTA) ID : 1170
find_fuzz(tmp_rta, 'ASEAN Free Trade Area')
# SACU ID : 7
find_fuzz(tmp_rta, 'Southern African Customs Union')
# Southern Common Market ID : 130
find_fuzz(tmp_rta, 'Southern Common Market')
# Central American Common Market ID : 151
find_fuzz(tmp_rta, 'Central American Common Market')
# Eurasian Economic Union ID : 909
find_fuzz(tmp_rta, 'Eurasian Economic Union')
# European Free Trade Association ID : 152
find_fuzz(tmp_rta, 'European Free Trade Association')
# Gulf Cooperation Council ID : 17
find_fuzz(tmp_rta, 'Gulf Cooperation Council')
# European Union ID : NONE
find_fuzz(tmp_rta, 'European Union', 'Current signatories')
# %% [markdown]
# ## get country names in EU
# %%
# ## 1. replace names not in baci with tmp_rta[rta_id][Current signatories] + EU's country names string
# ## 2. map above string to country codes
# ## 3. create list of country codes, NMI with product network

# tmp_RTA_ids = [1170, 7, 130, 151, 909, 152, 17]
# tmp_dict = {}
# for rta_id in tmp_RTA_ids:
#     countries_str = tmp_rta[tmp_rta['RTA ID'] == rta_id]['Current signatories'].values[0]
#     print(countries_str)





# %% [markdown]
# やること：(1/9)
# 1. 2016-2019の間にEntry/ExitがあったRTAを抽出
#   1. ID: 994, 640, 953, 692, 469, 759, 897, 681, 901
#   2. 2016, 2017, 2018, 2019のそれぞれの年について、変化を反映させたRTAシートを作る
# 2. RTAの国をCodeに変換
#   1. RTAの国のリストを作る
#       1. to_csv
#   2. RTAの国のリストをCodeに変換
# 3. RTAのネットワークを作る
# %%

has_exits_post_2016_filter = (rta['Specific Entry/Exit dates'].notna()).values
# tmp_rta = rta[sign_pre_2016_filter & active_post_2016_filter]
# tmp_rta = rta[inactive_post_2016_filter]


# %%
G = nx.Graph()
economy_nodes = list(dist_df_inv['economy'].unique())
partner_nodes = list(dist_df_inv['partner'].unique())
G.add_nodes_from(economy_nodes, node_type='export')
G.add_nodes_from(partner_nodes, node_type='import')
for index, row in dist_df_inv.iterrows():
    exporter = row['economy']
    importer = row['partner']
    dist_inv = row['dist_inv']
    G.add_edge(exporter, importer, weight=dist_inv)
