import pandas as pd
import numpy as np

import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from warnings import filterwarnings
filterwarnings('ignore')


# BASIC PREPROCESSING
def replace_0(string):
    try:
        return int(string.replace('0000u', '0'))
    except:
        return string

def replace_Estimated(string):
    if string == 'Estimated':
        return 1
    else:
        return 0

# FOR GETTING PRODUCT DF
def get_commodity_codes(
    csvs_root='../../csvs/'
    ):

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

    return commodity_code

def get_countries(
    data_root='../../../../data/trade/BACI/'
    ):

    country_df = pd.read_csv(
        data_root + 'countries.csv'
        )
    countries = country_df.Name.values
    countries = np.append(countries, ["United States of America", "China, Hong Kong SAR", "China, Taiwan Province of", "Türkiye", "Iran (Islamic Republic of)", "Czechia", "Switzerland, Liechtenstein", "China, Macao SAR", "Korea, Dem. People's Rep. of", "Venezuela (Bolivarian Rep. of)", "Côte d'Ivoire", "Congo, Dem. Rep. of the", "Lao People's Dem. Rep.", "Bolivia (Plurinational State of)", "North Macedonia", "Curaçao", "State of Palestine", "Cabo Verde", "Eswatini", "British Virgin Islands", "Micronesia (Federated States of)", "Wallis and Futuna Islands", "Holy See",])
    return countries


def get_product_data(
        exports=True, 
        imports=True,
        csvs_root='../../csvs/', # these roots are relative to .py files in workspace
        data_root='../../../../data/trade/BACI/',
        data_file_name='product_2017_19.csv'
    ):

    products = pd.read_csv(
        csvs_root+data_file_name,
        dtype={'product': object, 'flow':int}
        )
    countries = get_countries(data_root)
    commodity_code = get_commodity_codes(csvs_root)

    # merge commodity codes
    products = products.merge(
        commodity_code, on='product', how='left')

    # limit to exports/imports
    if exports and imports:
        print('using both exports and imports')
        pass
    elif exports:
        products = products[products['flow']==2]
    elif imports:
        products = products[products['flow']==1]

    # --- 11/23 ---
    # COMMENTED OUT BELOW FOR GETTING PARTNER: 'WORLD'
    # -------------
    # # limit to countries
    # partner_country_filter = \
    #     (products['partner_label'].isin(countries))
    # economy_filter = \
    #     (products['economy_label'].isin(countries))
    # products = \
    #     products[partner_country_filter & economy_filter]
    #
    # # drop columns that aren't included in commodity codes
    # products.dropna(subset=['Classification'], inplace=True)
    # # limit to level3
    # products = \
    #     products[products.Level==3]
    
    return products

# FOR GETTING NETWORK
def create_network(year, product_name, product_df):
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
        G,  # product network
        product_name,
        country,
        product_df,
        degree_type='out'
    ):
    

    # compute degree centrality of China
    if degree_type=='out':
        dc = nx.out_degree_centrality(G)
    elif degree_type=='in':
        dc = nx.in_degree_centrality(G)
    else:
        dc = nx.degree_centrality(G)

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
    
    return country_dc, country_ec


def aggregate_products(products):
    aggregated = products.groupby(
        ['year', 'economy_label', 'product', 'product_label']
        ).agg({'KUSD':'sum'}).reset_index()
    return aggregated

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
