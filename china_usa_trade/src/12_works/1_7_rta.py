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
products = products[products['Level']==3]
products = products.dropna(subset=['Code_economy', 'Code_partner']) # limit to countries
products = products[products['partner_label'] != products['economy_label']]
# %% 
# preventing namibia(NA) from being nan
# by default, there are no nans in other columns
geos = pd.read_csv(csvs_root + 'geo_cepii.csv', keep_default_na=False)
geos.head()
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
dist_df_inv = dist_df.copy()
dist_df_inv['dist_inv'] = dist_df_inv['dist'].apply(lambda x: 1/x)

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
