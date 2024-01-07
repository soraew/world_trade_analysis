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
from hfuncs.plotting_communities import *

# %%
# # load data
csvs_root= '../../csvs/'
data_root= '../../../../data/trade/BACI/'
data_file_name='total_764_2016_21.csv'

products = get_product_data(
    exports=True,
    imports=True,
    csvs_root=csvs_root,
    data_root=data_root,
    data_file_name=data_file_name,
)
countries = get_countries(data_root=data_root)
country_df = pd.read_csv(data_root + 'countries.csv')

# %%
products_economy_labeled = products.merge(
    country_df,
    left_on='economy_label',
    right_on='Name',
    how='left')
products_labeled = products_economy_labeled.merge(
    country_df,
    left_on='partner_label',
    right_on='Name',
    how='left',
    suffixes=('_economy', '_partner'))
products = products_labeled.copy()
del(products_economy_labeled)
del(products_labeled)
# %%
# products = products[products['Level']==3]
products = products.dropna(subset=['Code_economy', 'Code_partner'])
products = products[products['partner_label'] != products['economy_label']]
# products = products[products['flow']==2]

# %%
def get_filter(products, product_code='764', year=2017, flow=False, percentile=0.9):
    year_filter = products['year'] == year
    product_filter = products['product'] == product_code
    if flow:
        flow_filter = products['flow'] == flow
        all_filters = flow_filter & year_filter & product_filter
    else:
        all_filters = year_filter & product_filter
    tmp_kusd = products[all_filters]['KUSD'].copy()
    tmp_kusd = tmp_kusd.values
    tmp_kusd = np.sort(tmp_kusd)[::-1]
    cumulative = np.cumsum(tmp_kusd)
    index = np.argmax(cumulative > percentile*np.sum(tmp_kusd))
    kusd_filter = tmp_kusd[index]
    return kusd_filter

# %% [markdown]
# # Plotting communities over years
# %%
# %%
FLOW = 1# 1: imports, 2: exports
FIGSIZE = (21, 21)
YEARS = (2016, 2017, 2019) 

PRODUCTS = [
    'TOTAL',
    '764', # Telecommunication equipment, n.e.s. & parts, ...
    # '776', # Cathode valves & tubes(semiconductors)
    # '778', # Electrical machinery & apparatus, n.e.s.
]
for product in PRODUCTS:
    KUSD_FILTER = \
        get_filter(
            products, product_code=product,
            year=2016, flow=FLOW, percentile=0.95)
    print('kusd_filter: ', KUSD_FILTER)
    plot_communities_years(
        years=YEARS,
        product_code=product,
        product_df=products[products['flow']==FLOW],
        # product_df=products,
        kusd_filter=KUSD_FILTER,
        figsize=FIGSIZE,
        label_columns=['Code_economy', 'Code_partner'],
        # label_columns=['economy_label', 'partner_label']
        # detection_type='gm',
        )


# %% [markdown]
# # Plotting top partners over years
# %% [markdown]
# ## Get top partners over years
# %%
def get_top_partners_over_years(
        product_df,
        YEARS,
        PRODUCT_CODE,
        ECONOMY,
        FLOW,
        N):
    product_filter = product_df['product']==PRODUCT_CODE
    economy_filter = product_df['economy_label']==ECONOMY
    flow_filter = product_df['flow']==FLOW
    years_filter = product_df['year'].isin(YEARS)
    all_filters = \
        product_filter & economy_filter & flow_filter & years_filter
    product_df = product_df[all_filters]
    product_df = product_df.sort_values(['year', 'KUSD'],
                        ascending=[True, False])
    country_top5_partners = \
        product_df.groupby('year').head(N).reset_index()
    top5_partners_over_years = country_top5_partners.partner_label.unique()
    return top5_partners_over_years

# %% [markdown]
# ## Plot top partners over years
# %%
plot_top_partners = False
if plot_top_partners:
    YEARS = (2017, 2018, 2019, 2021)
    PRODUCT_CODE = '764'
    ECONOMY = "United States of America"
    # ECONOMY = "China"
    ECONOMY = "Japan"
    FLOW = 1
    N = 5
    product_df = products.copy()
    for product in PRODUCTS:
        top_partners = get_top_partners_over_years(
            product_df=products,
            YEARS=YEARS,
            PRODUCT_CODE=product,
            ECONOMY=ECONOMY,
            FLOW=FLOW,
            N=5)
        product_filter = products['product']==product
        flow_filter = products['flow']==FLOW
        importer_filter = products['economy_label']==ECONOMY

        exporter_filter = products['partner_label'].isin(top_partners)
        all_filters = product_filter & importer_filter & exporter_filter & flow_filter

        tmp_products = products[all_filters].copy()
        tmp_products['year'] = tmp_products['year'].astype(str)
        flow_name = 'Exports' if FLOW==2 else 'Imports'
        fig = px.line(
            tmp_products,
            x='year',
            y='KUSD',
            color='partner_label',
            title=f'{product} Top {N} {flow_name} partners of {ECONOMY}',
            markers=True,
            )
        fig.show()

# %%
