# %%
import pandas as pd
import numpy as np
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


csvs_root= '../../csvs/'
data_root= '../../../../data/trade/BACI/'
data_file_name='product_2017_19.csv'

# ONLY EXPORTS
products = get_product_data(
    exports=True,
    imports=False,
    csvs_root=csvs_root,
    data_root=data_root,
    data_file_name=data_file_name,
)

aggregated = aggregate_products(products)

chinese_top5_2017, chinese_productlabels_top5_2017 = \
    top_products(aggregated, 'China', 2017)
usa_top5_2017, usa_productlabels_top5_2017 = \
    top_products(aggregated, 'United States of America', 2017)

tele_product_code = chinese_top5_2017[0]
tele_product_label = chinese_productlabels_top5_2017[0]

tele_G = create_network(
    2017,
    tele_product_code,
    product_df=products)

# %% [markdown]
# ### is united states trading with china-affiliated countries?
# %%
# get top countries us imports telecomm from(2017)

tele_products_2017 = \
    tele_products[tele_products['year']==2017]
top_us_importers_2017 = \
    tele_products_2017[\
        tele_products_2017['partner_label']=='United States of America']\
            .sort_values('KUSD', ascending=False)\
            .head(10).economy_label.values.tolist()
top_us_oc_subG = \
    create_output_complete_subG(
        tele_G,
        top_us_importers_2017)
# plot
top_us_oc_subG = filter_edges(top_us_oc_subG, min_kusd=1e6)
plot_subG(top_us_oc_subG, scaler=1)
# print(check_gamma(top_us_oc_subG))
gamma, ncountries, nflows, ncycles, cycles = check_gamma(top_us_oc_subG)
print(gamma, ncountries, nflows, ncycles)
print(top_us_importers_2017)

#%%



## TODO
# - [ ] look at supply chain
# - [ ] read about resillience of trade
#     - [ ] ![GVC](https://www.oecd-ilibrary.org/science-and-technology/global-value-chain-dependencies-under-the-magnifying-glass_b2489065-en)
#     - [ ] ![review_2015](../../refs/supply_chain_resillience.pdf)
#     - [ ] localization
