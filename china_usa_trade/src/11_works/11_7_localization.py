# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from warnings import filterwarnings
filterwarnings('ignore')

from hfuncs.preprocessing import *
from hfuncs.plotting import *


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

def top_products(aggregated, country, year, n=5):
    country_exports = \
        aggregated[aggregated['economy_label']==country]\
            .sort_values(['year', 'KUSD'], ascending=[True, False])
    country_top5 = \
        country_exports.groupby('year').head(n).reset_index()
    country_top5_year_product_codes = \
        country_top5[country_top5['year']==year]\
        ['product'].values
    country_top5_year_product_labels = \
        country_top5[country_top5['year']==year]\
        ['product_label'].values
    return country_top5_year_product_codes, country_top5_year_product_labels

chinese_top5_2017, chinese_productlabels_top5_2017 = \
    top_products(aggregated, 'China', 2017)
usa_top5_2017, usa_productlabels_top5_2017 = \
    top_products(aggregated, 'United States of America', 2017)


country = 'China'
product_name = chinese_top5_2017[0]
product_label = chinese_productlabels_top5_2017[0]

ch_G = create_network(
    2017,
    product_name,
    product_df=products)

# create subgraph
select_nodes = False
if select_nodes:
    asia = [
        'China',
        'China, Hong Kong SAR',
        'Singapore',
        'Indonesia',
        'Viet Nam',
        'New Zealand',
        'India',
        'Japan',
        'Sri Lanka',
        'Australia',
        'Malaysia',
        'Philippines',
        'Korea, Republic of',
        'Thailand',
        'China, Taiwan Province of']
    select_countries = asia
    ch_G_sub = ch_G.subgraph(select_countries)
else:
    ch_G_sub = ch_G.copy()
min_kusd = 500000
new_edges = \
    [(u, v) for u, v, d in ch_G_sub.edges(data=True) if d['weight'] >= min_kusd]
ch_G_sub = ch_G.edge_subgraph(new_edges)

# plot
position = nx.circular_layout(ch_G_sub, scale=1.5)
weights = \
    get_weights_for_plotting(
    ch_G_sub,
    scaler=3.0)
fig, ax = plot_directed_network(
    ch_G_sub,
    ch_G_sub.nodes(),
    position,
    weights)


country = 'United States of America'
product_name = usa_top5_2017[0]
product_label = usa_productlabels_top5_2017[0]
usa_G = create_network(
    2017,
    product_name,
    product_df=products)
select_countries = [
    'United States of America',
    'Japan',
    'Saudi Arabia',
    'China', ]



## TODO
# - [ ] plot oil network
# - [ ] look at supply chain
# - [ ] read about resillience of trade
#     - [ ] ![GVC](https://www.oecd-ilibrary.org/science-and-technology/global-value-chain-dependencies-under-the-magnifying-glass_b2489065-en)
#     - [ ] ![review_2015](../../refs/supply_chain_resillience.pdf)
#     - [ ] localization
# - [ ] decompose adjacency matrix
#     - [ ] k_core?
#       - [ ] G.remove_edges_from(nx.selfloop_edges(G))
#       - [ ] G_core = nx.k_core(G)
#       - [ ] k = 200
#           - why is this greater than 180?(all countries)
#     - [ ] create subgraph
# - [ ] localized network
#     - [ ] output complete
#         - [ ] all flows involving m are included
#     - [ ] -|ncountries| + |nflows| - |ncycles|


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



breakpoint()



