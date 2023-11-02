# %%
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from warnings import filterwarnings
filterwarnings('ignore')


## PREPROCESSING
# load data
csvs_root= '../../csvs/'
data_root= '../../../../data/trade/BACI/'

products = pd.read_csv(
    csvs_root+'product_2017_19.csv',
    dtype={'product': object, 'flow':int}
    )

commodity_code = pd.read_csv(
    csvs_root+'commodity_code.csv',
    encoding='latin-1',
    dtype={'Code': object, 'isLeaf':int, 'Level':int},
    )
commodity_code = \
    commodity_code[commodity_code['Classification']=='S3']
commodity_code = commodity_code.iloc[:, :-1]
commodity_code.rename(
    columns={'Code': 'product'}, inplace=True)

country_df = pd.read_csv(
    data_root + 'countries.csv'
    )
countries = country_df.Name.values
countries = np.append(countries, ["United States of America", "China, Hong Kong SAR", "China, Taiwan Province of", "Türkiye", "Iran (Islamic Republic of)", "Czechia", "Switzerland, Liechtenstein", "China, Macao SAR", "Korea, Dem. People's Rep. of", "Venezuela (Bolivarian Rep. of)", "Côte d'Ivoire", "Congo, Dem. Rep. of the", "Lao People's Dem. Rep.", "Bolivia (Plurinational State of)", "North Macedonia", "Curaçao", "State of Palestine", "Cabo Verde", "Eswatini", "British Virgin Islands", "Micronesia (Federated States of)", "Wallis and Futuna Islands", "Holy See",])

# merge commodity codes
products = products.merge(
    commodity_code, on='product', how='left')

# # limit to exports
# products = products[products['flow']==2]

# limit to countries
partner_country_filter = \
    (products['partner_label'].isin(countries))
economy_filter = \
    (products['economy_label'].isin(countries))
products = \
    products[partner_country_filter & economy_filter]

# drop columns that aren't included in commodity codes
products.dropna(subset=['Classification'], inplace=True)

# limit to level3
products = \
    products[products.Level==3]

# %%
## CHINA/USA'S BIGGEST EXPORTS

aggregated = products.groupby(
    ['year', 'economy_label', 'product', 'product_label']
    ).agg({'KUSD':'sum'}).reset_index()

chinas_exports = \
    aggregated[aggregated['economy_label']=='China']\
        .sort_values(['year', 'KUSD'], ascending=[True, False])


# china's top5 exports in 2017
chinese_top5 = \
    chinas_exports.groupby('year').head(5).reset_index()
chinese_top5_2017 = \
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

def create_network(year, product_name, product_df=products):
    filter_product = \
        (product_df['product']==product_name).values
    filter_year = \
        (product_df['year']==year).values 
    product_df_cp = product_df[filter_product & filter_year]\
        [[
            'economy_label',
            'partner_label',
            'KUSD'
        ]].copy()
    # create network
    G = nx.DiGraph()
    export_nodes = list(product_df_cp.economy_label.unique())
    import_nodes = list(product_df_cp.partner_label.unique())
    G.add_nodes_from(export_nodes, node_type='export')
    G.add_nodes_from(import_nodes, node_type='import')

    for index, row in product_df_cp.iterrows():
        exporter = row['economy_label']
        importer = row['partner_label']
        kusd = row['KUSD']
        G.add_edge(exporter, importer, weight=kusd)

    return G

def degree_eigen_centrality(
        year,
        product_name,
        country,
        product_df=products):
    
    # filter_product = \
    #     (product_df['product']==product_name).values
    # filter_year = \
    #     (product_df['year']==year).values 
    # product_df_cp = product_df[filter_product & filter_year]\
    #     [[
    #         'economy_label',
    #         'partner_label',
    #         'KUSD'
    #     ]].copy()
    #
    # # create network
    # G = nx.DiGraph()
    # export_nodes = list(product_df_cp.economy_label.unique())
    # import_nodes = list(product_df_cp.partner_label.unique())
    # G.add_nodes_from(export_nodes, node_type='export')
    # G.add_nodes_from(import_nodes, node_type='import')
    G = create_network(
        year, 
        product_name, 
        product_df=product_df)

    for index, row in product_df_cp.iterrows():
        exporter = row['economy_label']
        importer = row['partner_label']
        kusd = row['KUSD']
        G.add_edge(exporter, importer, weight=kusd)

    # compute degree centrality of China
    dc = nx.out_degree_centrality(G)
    df_dc = \
        pd.DataFrame.from_dict(dc, orient='index', columns=['out_degree_centrality'])
    df_dc = df_dc.reset_index().rename({'index': 'economy_label'}, axis=1)
    df_dc = df_dc.sort_values(by=['out_degree_centrality'], ascending=False)
    country_dc = \
        df_dc[df_dc['economy_label']==country]['out_degree_centrality'].values[0]
    print(f"{country}'s out_degree centrality: {round(country_dc, 5)}")

    # compute eigenvector centrality of China
    ec = nx.eigenvector_centrality(G)
    df_ec = \
        pd.DataFrame.from_dict(ec, orient='index', columns=['eigenvector_centrality'])
    df_ec = df_ec.reset_index().rename({'index': 'economy_label'}, axis=1)
    df_ec = df_ec.sort_values(by=['eigenvector_centrality'], ascending=False)
    country_ec = \
        df_ec[df_ec['economy_label']==country]['eigenvector_centrality'].values[0]
    print(f"{country}'s eigenvector centrality: {round(country_ec, 5)}")
    
    return country_dc, country_ec, G



country = 'China'
dc_fig = go.Figure()
ec_fig = go.Figure()

for product_name, product_label in \
    zip(chinese_top5_2017, chinese_productlabels_top5_2017):

    ch_2017_dc, ch_2017_ec, ch_2017_G = \
        degree_eigen_centrality(2017, product_name, country, products)
    ch_2018_dc, ch_2018_ec, ch_2018_G = \
        degree_eigen_centrality(2018, product_name, country, products)
    ch_2019_dc, ch_2019_ec, ch_2019_G = \
        degree_eigen_centrality(2019, product_name, country, products)

    dc_fig.add_trace(go.Scatter(
        x=[2017, 2018, 2019],
        y=[ch_2017_dc, ch_2018_dc, ch_2019_dc],
        name=product_label,
        mode="markers+lines"))

    ec_fig.add_trace(go.Scatter(
        x=[2017, 2018, 2019],
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

    usa_2017_dc, usa_2017_ec, usa_2017_G = \
        degree_eigen_centrality(2017, product_name, country, products)
    usa_2018_dc, usa_2018_ec, usa_2018_G = \
        degree_eigen_centrality(2018, product_name, country, products)
    usa_2019_dc, usa_2019_ec, usa_2019_G = \
        degree_eigen_centrality(2019, product_name, country, products)

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

edges = G.edges()
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


