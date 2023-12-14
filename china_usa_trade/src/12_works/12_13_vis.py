# %%
import pandas as pd
import numpy as np
import matplotlib
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
data_file_name='product_2017_21.csv'

# ONLY EXPORTS
products = get_product_data(
    exports=True,
    imports=True,
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
index = 0
tele_product_code = chinese_top5_2017[0]
tele_product_label = chinese_productlabels_top5_2017[0]
tele_products = products[products['product']==tele_product_code]

kusd_filter = 1e5
print(tele_products[tele_products['KUSD']>=kusd_filter]['KUSD'].sum()\
    /tele_products['KUSD'].sum())
tele_prodcuts = tele_products[tele_products['KUSD']>=kusd_filter]

# %%
tele_products = tele_products[tele_products['KUSD']>=1e5]
tele_products = tele_products[tele_products['flow']==2]
# %%
year1 = 2018
year2 = 2021
tele_products = tele_products[['year', 'product', 'economy_label', 'partner_label', 'KUSD']]
tele_1_2 = pd.merge(
    tele_products[tele_products['year'] == year2],
    tele_products[tele_products['year'] == year1],
    on=['product', 'partner_label', 'economy_label'],
    how='inner',
    suffixes=('_2', '_1'))
tele_1_2['KUSD'] = \
    tele_1_2['KUSD_2'] - tele_1_2['KUSD_1']

tele_1_2 = tele_1_2[['product', 'economy_label', 'partner_label', 'KUSD']]
tele_1_2['year'] = year2
#%%
fig = px.histogram(tele_1_2, x='KUSD')
fig.show()
tele_1_2.sort_values(by='KUSD', ascending=True).head(20)

#%%
sub_diff = create_network(
    year2,
    tele_product_code,
    product_df=tele_1_2[tele_1_2['KUSD']>=1e5])

# %%
tele_sub_G = filter_edges(sub_diff, min_kusd=1e5)
c = nx.community.greedy_modularity_communities(tele_sub_G)
colorscheme = 'Set1'
cmap = plt.get_cmap(colorscheme)
colors = [cmap(i) for i in np.linspace(0.2, 0.7, len(c))]

for i, community in enumerate(c):
    figsize = (14, 14)
    fig, ax = plt.subplots(figsize=figsize)

    community = list(community)
    # tmp_colors = [colors[i] for k in range(len(community))]

    # G_sub = tele_sub_G
    # select_countries = tele_sub_G.nodes
    G_sub = tele_sub_G.subgraph(community)
    select_countries = community
    position = nx.circular_layout(G_sub, scale=2.5)
    weights = \
        get_weights_for_plotting(G_sub, scaler=2.0)

    nx.draw_networkx_nodes(
        G_sub,
        pos=position,
        node_color=colors[i],
        ax=ax,)
    nx.draw_networkx_labels(
        G_sub,
        labels=dict(zip(select_countries, select_countries)),
        pos=position,
        font_size=11,
        ax=ax,)
    nx.draw_networkx_edges(
        G_sub, position,
        edgelist=G_sub.edges(),
        width=weights,
        connectionstyle="arc3,rad=0.1",
        ax=ax)

