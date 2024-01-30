import pandas as pd
import numpy as np

import networkx as nx
from warnings import filterwarnings
filterwarnings('ignore')

from hfuncs.plotting_communities import plot_basic_communities, \
    get_louvain_partition, plot_communities_geo
from hfuncs.others import find_fuzz

# funtions for preprocessing rta data
def minus_100y(date):
    if date.year > 2023:
        return date - pd.offsets.DateOffset(years=100)
    else:
        return date

# BASIC PREPROCESSING => tmp_rta
def preprocess_rta(rta):
    rta['date_of_sign_G'] = \
        pd.to_datetime(rta['Date of Signature (G)'], format='%d-%b-%y', errors='coerce')
    rta['date_of_sign_S'] = \
        pd.to_datetime(rta['Date of Signature (S)'], format='%d-%b-%y', errors='coerce')
    rta['inactive_date'] = \
        pd.to_datetime(rta['Inactive Date'], format='%d-%b-%y', errors='coerce')
    rta['date_of_entry_into_force_G'] = \
        pd.to_datetime(rta['Date of Entry into Force (G)'], format='%d-%b-%y', errors='coerce')
    rta['date_of_sign_G'] = rta['date_of_sign_G'].apply(lambda x: minus_100y(x))
    rta['date_of_sign_S'] = rta['date_of_sign_S'].apply(lambda x: minus_100y(x))
    rta['inactive_date'] = rta['inactive_date'].apply(lambda x: minus_100y(x))

    # sign_pre_2016_filter = (rta['date_of_sign_G'] < pd.to_datetime('2016-01-01')).values

    inactive_between_2016_2021_filter = \
        (rta['inactive_date'] >= pd.to_datetime('2016-01-01')).values & \
        (rta['inactive_date'] < pd.to_datetime('2022-01-01')).values # 2016-21の間にinactive
    inactive_post_2021_filter = \
        (rta['inactive_date'] >= pd.to_datetime('2022-01-01')).values # 2021年以降にinactive
    post_2021_add_filter = \
        inactive_post_2021_filter & ~inactive_between_2016_2021_filter

    currently_active_filter = (rta['Status'] == 'In Force').values
    use_filter = (post_2021_add_filter | currently_active_filter) # & sign_pre_2016_filter

    tmp_rta = rta[use_filter]
    tmp_rta = tmp_rta[['RTA ID', 'RTA Name', 'Status', 'date_of_sign_G',
               'inactive_date', 'Original signatories', 'Current signatories',
               'Specific Entry/Exit dates', 'Coverage', 'Type']]
    return tmp_rta

# REPLACE ABBREVIATIONS WITH COUNTRIES => tmp_rta_new
# dict for replacing abbreviations with countries
def abbv_to_countries_dict(
        tmp_rta,
        EU_countries_str = 'Austria; Belgium; Cyprus; Czech Republic; Denmark; Estonia; Finland; France; Germany; Greece; Hungary; Ireland; Italy; Latvia; Lithuania; Luxembourg; Malta; Netherlands; Poland; Portugal; Slovak Republic; Slovenia; Spain; Sweden; United Kingdom',
        abbv_RTA_ids=[1170, 7, 130, 151, 909, 152, 17]
    ):
    abbv_rta_dict = {}
    for rta_id in abbv_RTA_ids:
        rta_name = \
            tmp_rta[tmp_rta['RTA ID'] == rta_id]['RTA Name'].values[0]
        countries_str = \
            tmp_rta[tmp_rta['RTA ID'] == rta_id]['Current signatories'].values[0]
        abbv_rta_dict[rta_name] = countries_str
    abbv_rta_dict['European Union'] = EU_countries_str
    return abbv_rta_dict

# replace abbreviation string with countries
def replace_abbv_with_country(string, rta_dict):
    if string is np.nan:
        return string
    for key, value in rta_dict.items():
        string = string.replace(key, value)
    return string
        
# replace abbreviations with countries
def replace_abbvs_with_countries(
        tmp_rta,
        EU_countries_str = 'Austria; Belgium; Cyprus; Czech Republic; Denmark; Estonia; Finland; France; Germany; Greece; Hungary; Ireland; Italy; Latvia; Lithuania; Luxembourg; Malta; Netherlands; Poland; Portugal; Slovak Republic; Slovenia; Spain; Sweden; United Kingdom',
        abbv_RTA_ids = [1170, 7, 130, 151, 909, 152, 17]
    ):
    abbv_rta_dict = abbv_to_countries_dict(tmp_rta, EU_countries_str, abbv_RTA_ids)
    tmp_rta_new = tmp_rta.copy()
    tmp_rta_new['Current signatories'] = tmp_rta['Current signatories'].\
        apply(lambda string: replace_abbv_with_country(string, abbv_rta_dict))
    return tmp_rta_new

# replace abbreviations with countries in rta df
def abbv_to_countries(tmp_rta, abbv_rta_dict):
    tmp_rta_new = tmp_rta.copy()
    tmp_rta_new['Current signatories'] = tmp_rta['Current signatories'].\
        apply(lambda string: replace_abbv_with_country(string, abbv_rta_dict))
    tmp_rta_new = replace_abbvs_with_countries(tmp_rta)
    return tmp_rta_new

# GET YEARLY RTA DF
def get_rta_year(tmp_rta_new, year='2017', git_csvs_root='../../csvs_git/'):
    rta_year = tmp_rta_new.copy()
    sign_pre_year_filter = \
        (rta_year['date_of_sign_G'] <= pd.to_datetime(f'{str(year)}-07-02')).values
    rta_year = rta_year[sign_pre_year_filter]
    if int(year) <= 2016:
        rta_year.at[692,'Current signatories'] = \
            rta_year.at[692,'Current signatories']\
                .replace('Ecuador;', '')
    # # from 2018
    if int(year) == 2017:
        rta_year.at[953,'Current signatories'] = \
            rta_year.at[953,'Current signatories']\
                .replace('Liechtenstein;', '').replace('Switzerland;', '')
        rta_year.at[897, 'Current signatories'] = \
            rta_year.at[897, 'Current signatories']\
                .replace('Mozambique;', '')
    # from 2019
    if int(year) <= 2018:
        rta_year.at[469,'Current signatories'] = \
            rta_year.at[469,'Current signatories']\
                .replace('Comoros;', '')
        if int(year) == 2018:
            rta_year.at[640,'Current signatories'] = \
                rta_year.at[640,'Current signatories']\
                    .replace('Viet Nam;', '')
            rta_year.at[901,'Current signatories'] = \
                rta_year.at[901,'Current signatories']\
                    .replace('Costa Rica', '')
            rta_year.at[994,'Current signatories'] = \
                rta_year.at[994,'Current signatories']\
                    .replace('Malaysia', '')
    # from 2020
    if int(year) <= 2019:
        rta_year.at[759,'Current signatories'] = \
            rta_year.at[759,'Current signatories']\
                .replace('Solomon Islands;', '')
    # # from 2021, 2022
    if int(year) <= 2020:
        if int(year) >= 2018:
            rta_year.at[640,'Current signatories'] = \
                rta_year.at[640,'Current signatories']\
                    .replace('Peru;', '').replace('Malaysia;', '')
            rta_year.at[901,'Current signatories'] = \
                rta_year.at[901,'Current signatories']\
                    .replace('Panama;', '')
            rta_year.at[994,'Current signatories'] = \
                rta_year.at[994,'Current signatories']\
                .replace('Cambodia;', '')
        if int(year) >= 2019:
            rta_year.at[1111,'Current signatories'] = \
                rta_year.at[1111,'Current signatories']\
                    .replace('Solomon Islands;', '').replace('Samoa;', '')
            
    # til 2021
    # United Kingdom
    if int(year) <= 2020:
        # til_2021 = pd.read_csv(git_csvs_root + 'tmp_find.csv', index_col=0)
        til_2021_uk=[6,12,18,33,44,52,63,68,73,77,91,92,93,107,109,111,112,114,
              118,123,132,137,138,142,143,144,145,148,154,167,386,564,605,619,
              623,680,712,836,847,848,849,850,869,872, 907,1002,1093,1094,1148]
        for i in til_2021_uk:
            try:
                if 'United Kingdom' in rta_year.at[i,'Current signatories']:
                    pass
            except:
                pass
            else:
                try:
                    rta_year.at[i,'Current signatories'] = \
                        rta_year.at[i,'Current signatories'] + 'United Kingdom;'
                    assert 'United Kingdom' in rta_year.at[i,'Current signatories']
                except:
                    pass

    return rta_year

# GET COUNTRY CODES PER RTA 
def get_country_codes_per_RTA(tmp_rta_new, rta_to_country_codes):
    country_codes_per_RTA = []
    # all_RTA_ids = tmp_rta_new['RTA ID'].unique()
    all_RTA_ids = tmp_rta_new.index.unique()
    rta_country_codes = set()
    # after adding abbvs
    for RTA_id in all_RTA_ids:
        # tmp_row = tmp_rta_new[tmp_rta_new['RTA ID'] == RTA_id]
        tmp_row = tmp_rta_new.loc[RTA_id]
        # tmp_str = tmp_row['Current signatories'].values[0]
        tmp_str = tmp_row['Current signatories']
        if tmp_str is np.nan: # only exception is NAFTA
            print('No Current signatories for:', tmp_row['RTA Name'])
            continue
        else:
            tmp_str_new = [x.strip() for x in tmp_str.split(';')]
            tmp_df = pd.DataFrame(tmp_str_new, columns=['country']).merge(
                rta_to_country_codes,
                left_on='country',
                right_on='RTA_country',
                how='left')
            # ↓remove RTA countries that didn't match with country codes
            tmp_df = tmp_df.dropna(subset=['Code_economy']) 
            tmp_df_codes = tmp_df['Code_economy'].values.tolist()
            country_codes_per_RTA.append(tmp_df_codes)
            rta_country_codes = rta_country_codes.union(set(tmp_df_codes))
    return rta_country_codes, country_codes_per_RTA

# CREATE RTA NETWORK
def create_rta_network(rta_country_codes, country_codes_per_RTA, weighted=False):
    G_rta = nx.Graph()
    economy_nodes = rta_country_codes
    G_rta.add_nodes_from(economy_nodes)
    edges_set = []
    for code_list in country_codes_per_RTA:
        for i in range(len(code_list)):
            for j in range(i+1, len(code_list)):
                if not weighted:
                    if set((code_list[i], code_list[j])) in edges_set:
                        continue
                    else: # add edge
                        G_rta.add_edge(code_list[i], code_list[j])
                        edges_set.append(set((code_list[i], code_list[j])))
                else:
                    G_rta.add_edge(code_list[i], code_list[j])
                    edges_set.append(set((code_list[i], code_list[j])))
    return G_rta

if __name__ == '__main__':
    csvs_root = '../../csvs/'
    git_csvs_root = '../../csvs_git/'

    # load and preprocess RTA data
    rta = pd.read_csv(csvs_root + 'AllRTAs_new.csv')
    tmp_rta = preprocess_rta(rta)


    # for converting RTA/ABBVs to countries
    EU_countries_str = 'Austria; Belgium; Cyprus; Czech Republic; Denmark; Estonia; Finland; France; Germany; Greece; Hungary; Ireland; Italy; Latvia; Lithuania; Luxembourg; Malta; Netherlands; Poland; Portugal; Slovak Republic; Slovenia; Spain; Sweden; United Kingdom'
    abbv_RTA_ids = [1170, 7, 130, 151, 909, 152, 17]
    abbv_rta_dict = abbv_to_countries_dict(tmp_rta, EU_countries_str, abbv_RTA_ids)

    # convert RTA/ABVVs to countries
    tmp_rta_new = abbv_to_countries(tmp_rta, abbv_rta_dict)
    # tmp_rta_new.reset_index(inplace=True, drop=True)
    # set RTA ID as index and sort by it
    tmp_rta_new.set_index('RTA ID', inplace=True)
    tmp_rta_new.sort_index(inplace=True)

    

    rta_16 = get_rta_year(tmp_rta_new, '2016')
    rta_17 = get_rta_year(tmp_rta_new, '2017')
    rta_18 = get_rta_year(tmp_rta_new, '2018')
    rta_19 = get_rta_year(tmp_rta_new, '2020')
    rta_20 = get_rta_year(tmp_rta_new, '2019')
    rta_21 = get_rta_year(tmp_rta_new, '2021')
    breakpoint()

    print('Samoa' in rta_19.at[131, 'Current signatories'])

    # get all RTAs in country codes
    rta_to_country_codes = pd.read_csv(git_csvs_root + 'rta_to_country_codes.csv')
    rta_country_codes_16, country_codes_per_RTA_16 = \
        get_country_codes_per_RTA(rta_16, rta_to_country_codes)
    rta_country_codes_17, country_codes_per_RTA_17 = \
        get_country_codes_per_RTA(rta_17, rta_to_country_codes)
    rta_country_codes_18, country_codes_per_RTA_18 = \
        get_country_codes_per_RTA(rta_18, rta_to_country_codes)
    rta_country_codes_19, country_codes_per_RTA_19 = \
        get_country_codes_per_RTA(rta_19, rta_to_country_codes)
    rta_country_codes_20, country_codes_per_RTA_20 = \
        get_country_codes_per_RTA(rta_20, rta_to_country_codes)
    rta_country_codes_21, country_codes_per_RTA_21 = \
        get_country_codes_per_RTA(rta_21, rta_to_country_codes)
    rta_16_G = create_rta_network(rta_country_codes_16, country_codes_per_RTA_16)
    rta_17_G = create_rta_network(rta_country_codes_17, country_codes_per_RTA_17)
    rta_18_G = create_rta_network(rta_country_codes_18, country_codes_per_RTA_18)
    rta_19_G = create_rta_network(rta_country_codes_19, country_codes_per_RTA_19)
    rta_20_G = create_rta_network(rta_country_codes_20, country_codes_per_RTA_20)
    rta_21_G = create_rta_network(rta_country_codes_21, country_codes_per_RTA_21)

    rta_16_partition = get_louvain_partition(rta_16_G)
    rta_17_partition = get_louvain_partition(rta_18_G)
    rta_18_partition = get_louvain_partition(rta_18_G)
    rta_19_partition = get_louvain_partition(rta_19_G)
    rta_20_partition = get_louvain_partition(rta_20_G)
    rta_21_partition = get_louvain_partition(rta_21_G)
    # plot_basic_communities(rta_16_G, rta_16_partition)
    # plot_basic_communities(rta_17_G, rta_17_partition)
    # plot_basic_communities(rta_18_G, rta_18_partition)
    # plot_basic_communities(rta_19_G, rta_19_partition)
    iso_corr = \
        pd.read_csv(
            git_csvs_root+'countries_iso2to3.csv',
            encoding="ISO-8859-1",
            keep_default_na=False) 
    tmp_dict = {2016: rta_16_partition, 2017: rta_17_partition,
                2018: rta_18_partition, 2019: rta_19_partition,
                2020: rta_20_partition, 2021: rta_21_partition}
    for year, product_partition in tmp_dict.items():
        plot_communities_geo(product_partition, iso_corr,
                             'RTA', year, show=False)

