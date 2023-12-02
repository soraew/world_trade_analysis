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


csvs_root= '../../csvs/'
data_root= '../../../../data/trade/BACI/'
data_file_name='product_2017_19.csv'

# ONLY EXPORTS
products = get_product_data(
    exports=False,
    imports=False,
    csvs_root=csvs_root,
    data_root=data_root,
    data_file_name=data_file_name,
)
countries = get_countries(data_root=data_root)

aggregated = aggregate_products(products)

chinese_top5_2017, chinese_productlabels_top5_2017 = \
    top_products(aggregated, 'China', 2017)
usa_top5_2017, usa_productlabels_top5_2017 = \
    top_products(aggregated, 'United States of America', 2017)

tele_product_code = chinese_top5_2017[0]
tele_product_label = chinese_productlabels_top5_2017[0]

# tele_df = \
#     products[products['product'] == tele_product_code]
# flow_filter = tele_df['flow'] == 1# imports
# year_filter = tele_df['year'] == 2017
# tele_df_filtered = \
#     tele_df[flow_filter & year_filter]
# Importer = 'United States of America'
# Exporter = 'China'

def get_DE(df, importer, exporter, product_code, flow=1, year=2017):
    tmp_df = df[
        (df['year'] == year).values\
        & \
        (df['product'] == product_code).values\
        & \
        (df['economy_label'] == importer).values\
        & \
        (df['flow'] == flow).values]
    total_imports = tmp_df[
        (tmp_df['partner_label'] == 'World').values\
        ]['KUSD'].values
    from_exporter = tmp_df[
        (tmp_df['partner_label'] == exporter).values\
        ]['KUSD'].values
    if len(total_imports) == 1 and len(from_exporter) == 1:
        total_imports = total_imports[0]
        from_exporter = from_exporter[0]
    elif len(total_imports) == 0 and len(from_exporter) == 1:
        return np.nan, 0
    elif len(from_exporter) == 0 and len(total_imports) == 1:
        return 0, total_imports
    elif len(from_exporter) == 0 and len(total_imports) == 0:
        return 0, 0

    return from_exporter / total_imports, total_imports

def get_exposures(df, intermediate_country, Importer, Exporter,
                  product_code, year):
    intermediate_exporter_exposure, \
    intermediate_total_imports = \
        get_DE(df,
            intermediate_country,
            Exporter,
            product_code,
            flow=1,
            year=year)
    importer_intermediate_exposure, \
    _ = \
        get_DE(df,
            Importer,
            intermediate_country,
            product_code,
            flow=1,
            year=year)
    _ ,\
    intermediate_total_exports = \
        get_DE(df,
            intermediate_country,
            'World',
            product_code,
            flow=2,
            year=year)
    if intermediate_total_exports == 0 and intermediate_total_imports > 0:
        intermediate_import_ratio = 1
    elif intermediate_total_exports == 0 and intermediate_total_imports == 0:
        intermediate_import_ratio = 0
    else:
        intermediate_import_ratio = \
            intermediate_total_imports / intermediate_total_exports
    if intermediate_import_ratio > 1:
        intermediate_import_ratio = 1
    ie = intermediate_exporter_exposure * \
        importer_intermediate_exposure * \
        intermediate_import_ratio
    return intermediate_exporter_exposure, \
        importer_intermediate_exposure, \
        intermediate_import_ratio, ie  

# %%
Importer = 'United States of America'
Exporter = 'China'
tele_df = products[products['product'] == tele_product_code]

exposure_over_years = []
direct_exposure_over_years = []
indirect_exposure_over_years = []
for year in (2017, 2018, 2019):
    intermediate_country_list = []
    intermediate_exporter_exposure_list = []
    importer_intermediate_exposure_list = []
    intermediate_import_ratio_list = []
    ie_list = []
    for i, intermediate_country in enumerate(tele_df['partner_label'].unique()):
        if intermediate_country not in [Importer, Exporter]\
            and intermediate_country in countries: 
            intermediate_exporter_exposure, \
            importer_intermediate_exposure, \
            intermediate_import_ratio, ie = \
                get_exposures(tele_df, intermediate_country, Importer, Exporter,
                            tele_product_code, year)

            # intermediate_country_list.append(intermediate_country)
            # intermediate_exporter_exposure_list.append(intermediate_exporter_exposure)
            # importer_intermediate_exposure_list.append(importer_intermediate_exposure)
            # intermediate_import_ratio_list.append(intermediate_import_ratio)
            ie_list.append(ie)
    direct_exposure = \
        get_DE(tele_df, Importer, Exporter, tele_product_code, 1, year)[0]
    direct_exposure_over_years.append(direct_exposure)
    indirect_exposure = sum(ie_list)[0]
    indirect_exposure_over_years.append(indirect_exposure)
# %%
intermediate_exposure_df = \
    pd.DataFrame(
        columns=['intermediate_country', 'intermediate_exporter_exposure',
                'importer_intermediate_exposure', 'intermediate_import_ratio', 'ie'])
intermediate_exposure_df['intermediate_country'] = \
    intermediate_country_list
intermediate_exposure_df['intermediate_exporter_exposure'] = \
    intermediate_exporter_exposure_list
intermediate_exposure_df['importer_intermediate_exposure'] = \
    importer_intermediate_exposure_list
intermediate_exposure_df['intermediate_import_ratio'] = \
    intermediate_import_ratio_list
intermediate_exposure_df['ie'] = ie_list
intermediate_exposure_df.sort_values(by=['ie'], ascending=False, inplace=True)

# %%
direct_exposure = get_DE(tele_df, Importer, Exporter, tele_product_code)[0]
total_exposure = \
    intermediate_exposure_df['ie'].sum() + direct_exposure
# %%
# ここ途中
fig = go.Figure()
fig.add_trace(go.Bar(
    x=intermediate_exposure_df['intermediate_country'],
    y=intermediate_exposure_df['ie'],
    name='Indirect Exposure',
    marker_color='indianred'
))
fig.add_trace(go.Bar(
    x=[Importer],
    y=[direct_exposure],
    name='Direct Exposure',
    marker_color='lightsalmon'
))
fig.add_trace(go.Bar(
    x=[Importer],
    y=[total_exposure],
    name='Total Exposure',
    marker_color='lightsalmon'
))
fig.update_layout(
    barmode='stack',
    title=f'Exposure of {Importer} to {Exporter} through {tele_product_label}',
    xaxis_title='Intermediate Country',
    yaxis_title='Exposure',
    legend_title='Exposure Type',
    font=dict(
        family="Courier New, monospace",
        size=18,
        color="RebeccaPurple"
    )
)
