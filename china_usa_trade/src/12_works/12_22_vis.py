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
products = products[products['Level']==3]
products = products[products['economy_label'].isin(countries)]
products = products[products['partner_label'].isin(countries)]
products = products[products['partner_label'] != products['economy_label']]

# %%
# limiting exports to 764's exports
# that are larger than 1e5k(100million) USD
tele_product_code = '764'
tele_products = products[products['product']==tele_product_code]
tele_product_label = \
    tele_products['product_label'].values[0]

kusd_filter = 1e5
print(tele_products[tele_products['KUSD']>=kusd_filter]['KUSD'].sum()\
    /tele_products['KUSD'].sum())

tele_products = tele_products[tele_products['KUSD']>=kusd_filter]
tele_products = tele_products[tele_products['flow']==2]
# %%
year1 = 2017
year2 = 2019
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
print('countries that trade dropped significantly: ')
tele_1_2.sort_values(by='KUSD', ascending=True).head(20)

#%%
tele_sub_G_17 = create_network(
    year1,
    tele_product_code,
    product_df=tele_products)
sub_diff = create_network(
    year2,
    tele_product_code,
    product_df=tele_1_2[tele_1_2['KUSD']>=1e5])

# %%
# tele_sub_G = filter_edges(sub_diff, min_kusd=1e5)
sub_G = tele_sub_G_17.copy()
plot_subG(
    sub_G,
    scaler=1.0,
    min_kusd=1e5,
    countries=False,
    figsize=(14, 14))
# %%
def plot_communities(G, min_kusd=1e5, figsize=(14, 14)):
    G = filter_edges(G, min_kusd)
    c = nx.community.greedy_modularity_communities(G)
    colorscheme = 'Set1'
    cmap = plt.get_cmap(colorscheme)
    colors = [cmap(i) for i in np.linspace(0.1, 0.9, len(c))]

    for i, community in enumerate(c):
        figsize = (14, 14)
        fig, ax = plt.subplots(figsize=figsize)

        community = list(community)

        sub_G_tmp = G.subgraph(community)
        select_countries = community
        position = nx.circular_layout(sub_G_tmp, scale=2.5)
        weights = \
            get_weights_for_plotting(sub_G_tmp, scaler=2.0)

        nx.draw_networkx_nodes(
            sub_G_tmp,
            pos=position,
            node_color=colors[i],
            ax=ax,)
        nx.draw_networkx_labels(
            sub_G_tmp,
            labels=dict(zip(select_countries, select_countries)),
            pos=position,
            font_size=11,
            ax=ax,)
        nx.draw_networkx_edges(
            sub_G_tmp, position,
            edgelist=sub_G_tmp.edges(),
            width=weights,
            connectionstyle="arc3,rad=0.1",
            ax=ax)
        plt.show()


# %%
