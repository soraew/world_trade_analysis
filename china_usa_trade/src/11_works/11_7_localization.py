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


# %% [markdown]
# # PREPROCESSING
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

# %% [markdown]
# # CHINA/USA'S BIGGEST EXPORT(TELECOMMUNICATION EQUIPMENT)
# %%
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


# %% [markdown]
# ## CREATE NETWORK
tele_product_code = chinese_top5_2017[0]
tele_product_label = chinese_productlabels_top5_2017[0]

tele_G = create_network(
    2017,
    tele_product_code,
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
    tele_subG = tele_G.subgraph(select_countries)
else:
    tele_subG = tele_G.copy()

def filter_nodes(G, countries):
    new_nodes = \
        [n for n in G.nodes() if n in countries]
    subG = G.subgraph(new_nodes)
    return subG

def filter_edges(G, min_kusd=50000):
    new_edges = \
        [(u, v) for u, v, d in G.edges(data=True) if d['weight'] >= min_kusd]
    subG = G.edge_subgraph(new_edges)
    return subG

def plot_subG(subG, scaler=1.0, min_kusd=50000, countries=False):
    if countries:
        subG = filter_nodes(subG, countries)
    if min_kusd:
        subG = filter_edges(subG, min_kusd=min_kusd)

    position = nx.circular_layout(subG, scale=1.5)
    weights = \
        get_weights_for_plotting(
        subG,
        scaler=scaler)
    fig, ax = plot_directed_network(
        subG,
        subG.nodes(),
        position,
        weights)
    return fig, ax

def create_output_complete_subG(G, countries):
    # create subgraph with all flows involving m
    subG = nx.DiGraph()
    for country in countries:
        subG.add_node(country)
    for edge in G.edges():
        if edge[0] in countries:
            subG.add_edge(
                edge[0], edge[1],
                weight=G.edges[edge]['weight'])
    return subG

def check_euler(subG):
    # check if output is complete
    # |ncountries| - |nflows| + |ncycles|
    # = 0
    n_countries = len(subG.nodes())
    n_flows = len(subG.edges())
    # n_cycles = nx.algorithms.cycles.find_cycle(subG)
    simple_cycles = nx.algorithms.cycles.simple_cycles(subG)
    n_cycles = len(list(simple_cycles))

    n_cycles = len(n_cycles)
    output_complete = n_countries - n_flows + n_cycles
    return output_complete

# %% [markdown]
# ## check okada
usca = \
    create_output_complete_subG(
        tele_subG,
        ['United States of America', 'Canada'])
subG = usca.copy()
subG.add_edge("Canada", "China",
              weight=3000000)
subG.add_edge("China", "United States of America",
              weight=3000000)
subG = filter_edges(subG, min_kusd=500000)
plot_subG(subG)
n_countries = len(subG.nodes())
n_flows = len(subG.edges())
simple_cycles = nx.algorithms.cycles.simple_cycles(subG)
n_cycles = len(list(simple_cycles))
output_complete = n_countries - n_flows + n_cycles
print(output_complete)


# country = 'United States of America'
# product_name = usa_top5_2017[0]
# product_label = usa_productlabels_top5_2017[0]
# usa_G = create_network(
#     2017,
#     product_name,
#     product_df=products)
# select_countries = [
#     'United States of America',
#     'Japan',
#     'Saudi Arabia',
#     'China', ]



## TODO
# - [ ] plot oil network
# - [ ] get product network again
#   - [ ] stop filtering with usa or china
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
# - [ ] **localized network**
#     - [ ] output complete
#         - [ ] all flows involving m are included
#     - [ ] -|ncountries| + |nflows| - |ncycles|
#     - [ ] try for us, canada first bc it has cycle





breakpoint()




# %%
