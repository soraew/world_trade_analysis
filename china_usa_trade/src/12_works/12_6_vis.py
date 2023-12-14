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

# %%
# # load data
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
countries = get_countries(data_root=data_root)
products = products[products['Level']==3]
products = products[products['economy_label'].isin(countries)]
products = products[products['partner_label'].isin(countries)]
products = products[products['partner_label'] != products['economy_label']]

# %%
aggregated = aggregate_products(products)
chinese_top5_2017, chinese_productlabels_top5_2017 = \
    top_products(aggregated, 'China', 2017)
usa_top5_2017, usa_productlabels_top5_2017 = \
    top_products(aggregated, 'United States of America', 2017)
tele_product_code = chinese_top5_2017[4]
tele_product_label = chinese_productlabels_top5_2017[4]
tele_products = products[products['product']==tele_product_code]

kusd_filter = 1e5
print(tele_products[tele_products['KUSD']>=kusd_filter]['KUSD'].sum()\
    /tele_products['KUSD'].sum())
tele_prodcuts = tele_products[tele_products['KUSD']>=kusd_filter]

# %%
tele_G = create_network(
    2017,
    tele_product_code,
    product_df=products)
tele_sub_G = filter_edges(tele_G, min_kusd=kusd_filter)
fig, ax = \
    plot_directed_network(
        tele_sub_G,
        tele_sub_G.nodes,
        # nx.spring_layout(tele_sub_G, scale=10000, iterations=1000),
        nx.circular_layout(tele_sub_G, scale=2.5),
        get_weights_for_plotting(tele_sub_G, scaler=2.0),
        figsize=(14, 14))
fig.suptitle(f'{tele_product_label[:20]}')
plt.show()