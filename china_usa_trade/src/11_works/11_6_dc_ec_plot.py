# %%
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from warnings import filterwarnings
filterwarnings('ignore')

from hfuncs.preprocessing_funcs import *


## PREPROCESSING
# load data
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

# %%
## CHINA/USA'S BIGGEST EXPORTS
aggregated = products.groupby(
    ['year', 'economy_label', 'product', 'product_label']
    ).agg({'KUSD':'sum'}).reset_index()

chinas_exports = \
    aggregated[aggregated['economy_label']=='China']\
        .sort_values(['year', 'KUSD'], ascending=[True, False])

# CHINA'S TOP5 EXPORTS IN 2017
chinese_top5 = \
    chinas_exports.groupby('year').head(5).reset_index()
chinese_top5_2017= \
    chinese_top5[chinese_top5['year']==2017]\
    ['product'].values
chinese_productlabels_top5_2017 = \
    chinese_top5[chinese_top5['year']==2017]\
    ['product_label'].values

usa_exports = \
    aggregated[aggregated['economy_label']=='United States of America']\
        .sort_values(['year', 'KUSD'], ascending=[True, False])
usa_top5 = \
    usa_exports.groupby('year').head(5).reset_index()
usa_top5_2017 = \
    usa_top5[usa_top5['year']==2017]\
    ['product'].values
usa_productlabels_top5_2017 = \
    usa_top5[usa_top5['year']==2017]\
    ['product_label'].values



# PLOT CHANGE IN DEGREE/EIGENVECTOR CENTRALITY FOR TOP5 PRODUCTS
country = 'China'
dc_fig = go.Figure()
ec_fig = go.Figure()
for product_name, product_label in \
    zip(chinese_top5_2017, chinese_productlabels_top5_2017):

    ch_2017_G = create_network(
        2017,
        product_name,
        product_df=products)
    ch_2018_G = create_network(
        2018,
        product_name,
        product_df=products)
    ch_2019_G = create_network(
        2019,
        product_name,
        product_df=products)

    ch_2017_dc, ch_2017_ec = \
        degree_eigen_centrality(ch_2017_G, product_name, country, products, False)
    ch_2018_dc, ch_2018_ec = \
        degree_eigen_centrality(ch_2018_G, product_name, country, products, False)
    ch_2019_dc, ch_2019_ec = \
        degree_eigen_centrality(ch_2019_G, product_name, country, products, False)

    dc_fig.add_trace(go.Scatter(
        x=['2017', '2018', '2019'],
        y=[ch_2017_dc, ch_2018_dc, ch_2019_dc],
        name=product_label,
        mode="markers+lines"))

    ec_fig.add_trace(go.Scatter(
        x=['2017', '2018', '2019'],
        y=[ch_2017_ec, ch_2018_ec, ch_2019_ec],
        name=product_label,
        mode="markers+lines"))

dc_fig.update_layout(
    title=f"{country}'s out-degree centrality for top products",
    xaxis_title="Year",
    yaxis_title="Out-degree centrality",)
dc_fig.show()

ec_fig.update_layout(
    title=f"{country}'s eigenvector centrality for top products",
    xaxis_title="Year",
    yaxis_title="Eigenvector centrality",)
ec_fig.show()


country = 'United States of America'
dc_fig = go.Figure()
ec_fig = go.Figure()

for product_name, product_label in \
    zip(usa_top5_2017, usa_productlabels_top5_2017):

    usa_2017_G = create_network(
        2017,
        product_name,
        product_df=products)
    usa_2018_G = create_network(
        2018,
        product_name,
        product_df=products)
    usa_2019_G = create_network(
        2019,
        product_name,
        product_df=products)

    usa_2017_dc, usa_2017_ec = \
        degree_eigen_centrality(usa_2017_G, product_name, country, products)
    usa_2018_dc, usa_2018_ec = \
        degree_eigen_centrality(usa_2018_G, product_name, country, products)
    usa_2019_dc, usa_2019_ec = \
        degree_eigen_centrality(usa_2019_G, product_name, country, products)

    dc_fig.add_trace(go.Scatter(
        x=[2017, 2018, 2019],
        y=[usa_2017_dc, usa_2018_dc, usa_2019_dc],
        name=product_label,
        mode="markers+lines"))

    ec_fig.add_trace(go.Scatter(
        x=[2017, 2018, 2019],
        y=[usa_2017_ec, usa_2018_ec, usa_2019_ec],
        name=product_label,
        mode="markers+lines"))

dc_fig.update_layout(
    title=f"{country}'s out-degree centrality for top products",
    xaxis_title="Year",
    yaxis_title="Out-degree centrality",
    yaxis_range=[0.8, 0.96])
dc_fig.show()

ec_fig.update_layout(
    title=f"{country}'s eigenvector centrality for top products",
    xaxis_title="Year",
    yaxis_title="Eigenvector centrality",
    yaxis_range=[0.113, 0.144])
ec_fig.show()

## TODO
# - [ ] localized network
#     - [ ] output complete
#         - [ ] all flows involving m are included
#     - [ ] -|ncountries| + |nflows| - |ncycles|

edges = usa_2017_G.edges()
def create_output_complete_subG(G, countries):
    # create subgraph with all flows involving m
    subG = nx.DiGraph()
    for country in countries:
        subG.add_node(country)
    for edge in G.edges():
        if edge[0] in countries:
            subG.add_edge(edge[0], edge[1])
    return subG


def check_output_complete(subG):
    # check if output is complete
    # -|ncountries| + |nflows| - |ncycles|
    # -|ncountries| + |nflows| - |nflows| + |ncountries| - |ncycles|
    # = 0
    n_countries = len(subG.nodes())
    n_flows = len(subG.edges())
    n_cycles = nx.algorithms.cycles.cycle_basis(subG)
    n_cycles = len(n_cycles)
    output_complete = -n_countries + n_flows - n_cycles
    return output_complete


