# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import pickle as pkl
from tqdm import tqdm
from warnings import filterwarnings
filterwarnings('ignore')
import os

from hfuncs.preprocessing import *
from hfuncs.plotting import *
from hfuncs.graphs import *


csvs_root= '../../csvs/'
data_root= '../../../../data/trade/BACI/'
data_file_name='top_ex_imp_2017_21.csv'

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

def get_IE_df(
        intermediate_country_list,
        intermediate_exporter_exposure_list,
        importer_intermediate_exposure_list,
        intermediate_import_ratio_list,
        ie_list):
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
    return intermediate_exposure_df

# %%

def get_exposures_over_years(products, Importer, Exporter, product_code, years):
    tmp_df = products[products['product'] == product_code]
    product_label = tmp_df['product_label'].unique()[0]

    direct_exposure_over_years = []
    indirect_exposure_over_years = []
    IE_dfs = []

    for year in tqdm(years):
        print(year)
        intermediate_country_list = []
        intermediate_exporter_exposure_list = []
        importer_intermediate_exposure_list = []
        intermediate_import_ratio_list = []
        ie_list = []
        for i, intermediate_country in enumerate(tmp_df['partner_label'].unique()):
            if intermediate_country not in [Importer, Exporter]\
                and intermediate_country in countries: 
                intermediate_exporter_exposure, \
                importer_intermediate_exposure, \
                intermediate_import_ratio, ie = \
                    get_exposures(tmp_df, intermediate_country, Importer, Exporter,
                                product_code, year)

                intermediate_country_list.append(intermediate_country)
                intermediate_exporter_exposure_list.append(intermediate_exporter_exposure)
                importer_intermediate_exposure_list.append(importer_intermediate_exposure)
                intermediate_import_ratio_list.append(intermediate_import_ratio)
                ie_list.append(ie)
        direct_exposure = \
            get_DE(tmp_df, Importer, Exporter, product_code, 1, year)[0]
        direct_exposure_over_years.append(direct_exposure)
        try:
            indirect_exposure = sum(ie_list)[0]
        except:
            indirect_exposure = sum(ie_list)
        indirect_exposure_over_years.append(indirect_exposure)
        IE_df = get_IE_df(intermediate_country_list, intermediate_exporter_exposure_list, importer_intermediate_exposure_list, intermediate_import_ratio_list, ie_list)
        IE_dfs.append(IE_df)

    years_dt = pd.to_datetime(years, format='%Y')
    fig=go.Figure()
    fig.add_trace(
        go.Bar(x=years_dt, y=direct_exposure_over_years, name='Direct'))
    fig.add_trace(
        go.Bar(x=years_dt, y=indirect_exposure_over_years, name='Indirect'))
    fig.update_layout(title=f'{product_label}')
    fig.show()
    return direct_exposure_over_years, indirect_exposure_over_years, IE_dfs, product_label
# %%
Importer = 'United States of America'
Exporter = 'China'
years = products.year.unique()

# %%
product_code = '764'
tele_DEs, tele_IEs, tele_IE_dfs, product_label = \
    get_exposures_over_years(products, Importer, Exporter, product_code, years)
# %%
product_code = '759'
parts_DEs, parts_IEs, parts_IE_dfs, product_label = \
    get_exposures_over_years(products, Importer, Exporter, product_code, years)
# %%
product_code = '752'
automatic_DEs, automatic_IEs, automatic_IE_dfs, product_label = \
    get_exposures_over_years(products, Importer, Exporter, product_code, years)
# %%
product_code = '778'
electrical_DEs, electrical_IEs, electrical_IE_dfs, product_label = \
    get_exposures_over_years(products, Importer, Exporter, product_code, years)
# %%
product_code = '821'
furniture_DEs, furniture_IEs, furniture_IE_dfs, product_label = \
    get_exposures_over_years(products, Importer, Exporter, product_code, years)
os.system('say "done"')

# %%
