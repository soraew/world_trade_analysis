# %%
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx
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
# BASIC FILTERING
products = products[products['Level']==3]
products = products[products['economy_label'].isin(countries)]
products = products[products['partner_label'].isin(countries)]
products = products[products['partner_label'] != products['economy_label']]
products = products[products['year'] != 2019]

# %%
# tele is #3 in US's imports
def get_country_partner_diffs_base(products, product_code, flow, economy_label):
    tele_products = products[products['product']==product_code]
    us_filter = \
        (tele_products['economy_label']==economy_label).values
    flow_filter = (tele_products['flow']==flow).values
    tele_products = tele_products[us_filter & flow_filter]
    return tele_products

def plot_top_partners_per_year(tele_products, top=5):
    top_importers = tele_products.groupby(['year', 'partner_label'])\
                    .agg(sum_kusd=('KUSD', 'sum'))\
                        .reset_index()\
                        .sort_values(
                            by=['year', 'sum_kusd'],
                            ascending=False)
    top_importers = top_importers.groupby('year').head(top)
    top_importers['year'] = pd.to_datetime(top_importers['year'],format='%Y')
    fig = px.line(
            top_importers,
            x='year',
            y='sum_kusd',
            color='partner_label',
            markers=True,
        )
    fig.show()

# %%
# tele is #3 in US's imports
tele_product_code = '764'
economy='United States of America'
flow=1 # imports
tele_products = \
    get_country_partner_diffs_base(
        products, tele_product_code, flow, economy)
# Mexico comes up as China drops, but plateaus from 2018 onwards
# China drops in 2019 but comes up again
plot_top_partners_per_year(tele_products, top=5)

# %%
# Auto is #4 in US's imports
auto_product_code = '752' # Automatic data processing machines
# plot x axis years, y axis kusd, color is country
economy='United States of America'
flow=1 # imports
auto_products = \
    get_country_partner_diffs_base(
        products, auto_product_code, flow, economy)
# Viet Nam comes up as China drops
# Mexico is somehow droping and plaeaus from 2019 onwards
plot_top_partners_per_year(auto_products, top=5)

# %%
# US top import countries and the amout that they traded
product_code = '781' # Motor vehicles(for persons)
economy = 'United States of America'
flow = 1 # imports
sub_products = \
    get_country_partner_diffs_base(
        products, product_code, flow, economy)
plot_top_partners_per_year(sub_products, top=5)

# %%
# tele is #1 in China's exports
tele_product_code = '764'
economy='China'
flow=2 # exports
tele_products = \
    get_country_partner_diffs_base(
        products, tele_product_code, flow, economy)
# Mexico comes up as China drops, but plateaus from 2028 onwards
# China drops in 2029 but comes up again
plot_top_partners_per_year(tele_products, top=20)

# %%
# Auto is #2s in China's exports
auto_product_code = '752' # Automatic data processing machines
# plot x axis years, y axis kusd, color is country
economy='China'
flow=2 # exports
auto_products = \
    get_country_partner_diffs_base(
        products, auto_product_code, flow, economy)
# Viet Nam comes up as China drops
# Mexico is somehow droping and plaeaus from 2029 onwards
plot_top_partners_per_year(auto_products, top=20)
# %%
