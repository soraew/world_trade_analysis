import pandas as pd
import numpy as np

import networkx as nx
from warnings import filterwarnings
filterwarnings('ignore')

from hfuncs.plotting_communities import plot_basic_communities, \
    get_louvain_partition

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

    sign_pre_2016_filter = (rta['date_of_sign_G'] < pd.to_datetime('2016-01-01')).values

    inactive_between_2016_2019_filter = \
        (rta['inactive_date'] > pd.to_datetime('2016-01-01')).values & \
        (rta['inactive_date'] < pd.to_datetime('2020-01-01')).values # 2016-19の間にinactive
    inactive_post_2019_filter = \
        (rta['inactive_date'] >= pd.to_datetime('2020-01-01')).values # 2016年以降にinactive
    post_2019_add_filter = \
        inactive_post_2019_filter & ~inactive_between_2016_2019_filter

    currently_active_filter = (rta['Status'] == 'In Force').values
    use_filter = (post_2019_add_filter | currently_active_filter) & sign_pre_2016_filter

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
    # breakpoint()
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
    if int(year) == 2017:
        rta_year.at[131,'Current signatories'] = \
            rta_year.at[131,'Current signatories']\
                .replace('Samoa;', '')
    if int(year) <= 2018:
        # from 2019
        rta_year.at[115,'Current signatories'] = \
            rta_year.at[115,'Current signatories']\
                .replace('Comoros;', '')
    if int(year) <= 2019:
        # from 2020
        rta_year.at[131,'Current signatories'] = \
            rta_year.at[131,'Current signatories']\
                .replace('Solomon Islands;', '')
    # til 2021
    # United Kingdom
    til_2021 = pd.read_csv(git_csvs_root + 'tmp_find.csv', index_col=0)
    for i in til_2021.index:
        if 'United Kingdom' in rta_year.at[i,'Current signatories']:
            pass
        else:
            rta_year.at[i,'Current signatories'] = \
                rta_year.at[i,'Current signatories'] + 'United Kingdom;'
            assert 'United Kingdom' in rta_year.at[i,'Current signatories']
    return rta_year

# GET COUNTRY CODES PER RTA 
def get_country_codes_per_RTA(tmp_rta_new, rta_to_country_codes):
    country_codes_per_RTA = []
    all_RTA_ids = tmp_rta_new['RTA ID'].unique()
    rta_country_codes = set()
    # after adding abbvs
    for RTA_id in all_RTA_ids:
        tmp_row = tmp_rta_new[tmp_rta_new['RTA ID'] == RTA_id]
        tmp_str = tmp_row['Current signatories'].values[0]
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
def create_rta_network(rta_country_codes, country_codes_per_RTA):
    G_rta = nx.Graph()
    economy_nodes = rta_country_codes
    G_rta.add_nodes_from(economy_nodes)
    edges_set = []
    for code_list in country_codes_per_RTA:
        for i in range(len(code_list)):
            for j in range(i+1, len(code_list)):
                if set((code_list[i], code_list[j])) in edges_set:
                    continue
                else: # add edge
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
    tmp_rta_new.reset_index(inplace=True, drop=True)

    rta_17 = get_rta_year(tmp_rta_new, '2017')
    rta_18 = get_rta_year(tmp_rta_new, '2018')
    rta_19 = get_rta_year(tmp_rta_new, '2019')
    print('Samoa' in rta_19.at[131, 'Current signatories'])

    # get all RTAs in country codes
    rta_to_country_codes = pd.read_csv(git_csvs_root + 'rta_to_country_codes.csv')
    rta_country_codes_17, country_codes_per_RTA_17 = \
        get_country_codes_per_RTA(rta_17, rta_to_country_codes)
    rta_country_codes_18, country_codes_per_RTA_18 = \
        get_country_codes_per_RTA(rta_18, rta_to_country_codes)
    rta_country_codes_19, country_codes_per_RTA_19 = \
        get_country_codes_per_RTA(rta_19, rta_to_country_codes)
    rta_17_G = create_rta_network(rta_country_codes_17, country_codes_per_RTA_17)
    rta_18_G = create_rta_network(rta_country_codes_18, country_codes_per_RTA_18)
    rta_19_G = create_rta_network(rta_country_codes_19, country_codes_per_RTA_19)

    rta_17_partition = get_louvain_partition(rta_18_G)
    rta_18_partition = get_louvain_partition(rta_18_G)
    rta_19_partition = get_louvain_partition(rta_19_G)
    plot_basic_communities(rta_17_G, rta_17_partition)
    plot_basic_communities(rta_18_G, rta_18_partition)
    plot_basic_communities(rta_19_G, rta_19_partition)

