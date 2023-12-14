# %% [markdown]
# # getting top 5 imports and exports for china and usa
# * not using 'World', aggregating using country data only
# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import pickle as pkl
from tqdm import tqdm
from warnings import filterwarnings
filterwarnings('ignore')
import os

from hfuncs.preprocessing import *
from hfuncs.plotting import *
from hfuncs.graphs import *

csvs_root= '../../csvs/'
data_root= '../../../../data/trade/BACI/'
data_file_name='product_2017_21.csv'

# ONLY EXPORTS
# products = get_product_data(
#     exports=False,
#     imports=False,
#     csvs_root=csvs_root,
#     data_root=data_root,
#     data_file_name=data_file_name,
# )
countries = get_countries(data_root=data_root)
commodity_code = get_commodity_codes(csvs_root=csvs_root)
# %%
def get_top_codes(df, countries, country, flow=1):
    if flow==1:
        print('imports')
    elif flow==2:
        print('exports')
    df = df[df.partner_label.isin(countries)]
    df = df[df['Level']==3]
    df = df[df.flow == flow]
    df = df[df['partner_label'] != country]
    df = df.sort_values(by='KUSD', ascending=False)
    top_df = df.groupby(['product', 'product_label'])\
        .agg(
            sum_kusd = ('KUSD', 'sum')
            ).reset_index().sort_values(by='sum_kusd', ascending=False)
    # return top_df.head(5)['product'].values.tolist()
    return top_df
# %%
us_trade_file_name = 'us_trade_2017.csv'
us_top = pd.read_csv(csvs_root+us_trade_file_name)
us_top = us_top.merge(
    commodity_code, on='product', how='left')
us_top_exports = \
    get_top_codes(us_top, countries, 'United States of America', flow=2)
us_top_export_codes = \
    us_top_exports.head(5)['product'].values.tolist()
us_top_imports = \
    get_top_codes(us_top, countries, 'United States of America', flow=1)
us_top_import_codes = \
    us_top_imports.head(5)['product'].values.tolist()
print('us_top_import_codes', us_top_import_codes)
print('us_top_export_codes', us_top_export_codes)
# us_top_import_codes ['781', '333', '764', '752', '542']
# us_top_export_codes ['334', '781', '776', '784', '764']
# %%

ch_trade_file_name = 'ch_trade_2017.csv'
ch_top = pd.read_csv(csvs_root+ch_trade_file_name)
ch_top = ch_top.merge(
    commodity_code, on='product', how='left')
ch_top_exports = \
    get_top_codes(ch_top, countries, 'China', flow=2)
ch_top_export_codes = \
    ch_top_exports.head(5)['product'].values.tolist()
ch_top_imports = \
    get_top_codes(ch_top, countries, 'China', flow=1)
ch_top_import_codes = \
    ch_top_imports.head(5)['product'].values.tolist()
print('ch_top_import_codes', ch_top_import_codes)
print('ch_top_export_codes', ch_top_export_codes)
# ch_top_import_codes ['776', '333', '281', '971', '781']
# ch_top_export_codes ['764', '752', '759', '776', '821']
# %%
top_export_imports = list(set(ch_top_import_codes + ch_top_export_codes +\
    us_top_import_codes + us_top_export_codes +\
        ['222', '334', '728', '752', '759', '764', '778', '784', '821', '874']))

top_export_imports

# %%
