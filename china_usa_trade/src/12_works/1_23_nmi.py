# %%
# imports
import pandas as pd

import plotly.express as px
import pickle as pkl

from sklearn.metrics import normalized_mutual_info_score as NMI

from warnings import filterwarnings
filterwarnings('ignore')

from hfuncs.preprocessing import *
from hfuncs.plotting import *
from hfuncs.graphs import *
from hfuncs.plotting_communities import *
from hfuncs.rta import *
from hfuncs.dist import *
from hfuncs.alliance import *

SHOW = False
SHOW_NMI = False
WRITE = False
LRN = 10
# YEARs = [2016]
YEARs = [2016, 2017, 2018, 2019, 2020, 2021]

# %%
# for loading data
csvs_root= '../../csvs/'
git_csvs_root = '../../csvs_git/'
data_root= '../../../../data/trade/BACI/'
images_root = 'images/communities2/'
nmi_images_root = 'images/nmis2/'
data_file_name='total_764_2016_21.csv'

# %%
# load and preprocess PRODUCT data
products, country_df = preprocess_products(
    exports=False,
    imports=True,
    csvs_root=csvs_root,
    data_root=data_root,
    data_file_name=data_file_name,)
products = products.dropna(subset=['Code_economy', 'Code_partner']) # limit to countries
products = products[products['partner_label'] != products['economy_label']]

iso_corr = \
    pd.read_csv(
        git_csvs_root+'countries_iso2to3.csv',
        encoding="ISO-8859-1",
        keep_default_na=False) 

def plot_communities_geo(
        product_partition,
        iso_corr,
        TYPE='Telecommunication equipment',
        YEAR=2017,
        show=False):
    comms = set(product_partition.values())
    ncomms = len(comms)
    tmp = pd.DataFrame(columns=['iso2', 'community'])

    # list of list of country codes
    for comm in comms:
        sublist = \
            [code for code in product_partition.keys() if \
                product_partition[code] == comm]
        community_arr = [str(comm)] * len(sublist)
        tmp_tmp = pd.DataFrame({'iso2': sublist, 'community': community_arr})
        tmp = pd.concat([tmp, tmp_tmp], axis=0)

    tmp_gpby_ordered = \
        tmp.groupby(['community']).count().reset_index()\
        .sort_values(by='iso2', ascending=False)
    tmp_gpby_ordered['community_new'] = np.arange(ncomms)
    tmp_gpby_ordered['community_new'] = tmp_gpby_ordered.apply(lambda row: row['community_new'] if \
        row['iso2'] > 1 else -1, axis=1)
    tmp = pd.merge(
        tmp, tmp_gpby_ordered[['community', 'community_new']],
        on='community', how='left')
    tmp = tmp.sort_values(by='community_new', ascending=True)
    tmp['community'] = tmp['community_new'].astype(str)

    # merge iso2 and iso3
    tmp = pd.merge(tmp, iso_corr, on='iso2', how='left')
    color_seq = px.colors.qualitative.Set1[:ncomms]
    fig = px.choropleth(
        locations=tmp['iso3'],
        color=tmp['community'],
        color_discrete_sequence=color_seq,
        locationmode='ISO-3',)
    if TYPE=='Telecommunication equipment' or TYPE=='RTA' or TYPE=='Total' and YEAR:
        title = f'{TYPE} communities in {YEAR}'
    else:
        title = f'{TYPE} communities'
    fig.update_layout(
        title_text=title,
        legend_title_text='community',
        geo=dict(
            showframe=False,
            showcoastlines=False,
            projection_type='equirectangular'),
        margin={'b':0}
        )
    if show:
        fig.show()
    return fig

def get_louvain_orig_partition(G):
    communities_orig = nx.community.louvain_communities(G)
    communities = list(communities_orig)
    partition = dict()
    for i, community in enumerate(communities):
        for country in community:
            partition[country] = i
    return partition, communities_orig
# %%

NMI_product_v_rta = []
NMI_product_v_dist = []
NMI_product_v_total = []
NMI_product_v_alliance = []

NMI_total_v_rta = []
NMI_total_v_dist = []
NMI_total_v_alliance = []
excluded_countries = []

# %%
# YEAR = 2017
for YEAR in YEARs:
    print(YEAR)
    # load and preprocess RTA data
    rta = pd.read_csv(csvs_root + 'AllRTAs_new.csv')
    tmp_rta = preprocess_rta(rta)

    # for converting RTA/ABBVs to countries
    EU_countries_str = 'Austria; Belgium; Cyprus; Czech Republic; Denmark; Estonia; Finland; France; Germany; Greece; Hungary; Ireland; Italy; Latvia; Lithuania; Luxembourg; Malta; Netherlands; Poland; Portugal; Slovak Republic; Slovenia; Spain; Sweden; United Kingdom'
    abbv_RTA_ids = [1170, 7, 130, 151, 909, 152, 17]
    abbv_rta_dict = \
        abbv_to_countries_dict(tmp_rta, EU_countries_str, abbv_RTA_ids)
    with open(git_csvs_root + 'abbv_rta_dict.pkl', 'wb') as f:
        pkl.dump(abbv_rta_dict, f)
    # breakpoint()


    # convert RTA/ABVVs to countries
    tmp_rta_new = abbv_to_countries(tmp_rta, abbv_rta_dict)
    tmp_rta_new.reset_index(inplace=True, drop=True)
    tmp_rta_new.set_index('RTA ID', inplace=True)
    tmp_rta_new.sort_index(inplace=True)
    rta_year = get_rta_year(tmp_rta_new, str(YEAR), git_csvs_root)

    # get all RTAs in country codes
    rta_to_country_codes = \
        pd.read_csv(git_csvs_root + 'rta_to_country_codes.csv')
    rta_country_codes_year, country_codes_per_rta_year = \
        get_country_codes_per_RTA(rta_year, rta_to_country_codes)
    rta_year_G = \
        create_rta_network(rta_country_codes_year, country_codes_per_rta_year, weighted=True)
    # rta_year_partition = get_louvain_partition(rta_year_G)
    rta_year_partition, rta_year_communities_orig = get_louvain_orig_partition(rta_year_G)
    #%%
    fig = plot_communities_geo(rta_year_partition, iso_corr, "RTA", YEAR)
    if WRITE:
        fig.write_image(images_root + f'rta_communities_{YEAR}.eps')  

    # %%
    # create product network
    # for YEAR in YEARs:
    product_G = create_network(
        YEAR,
        '764',
        products,
        ['Code_economy', 'Code_partner'])
    total_G = create_network(
        YEAR,
        'TOTAL',
        products[products['KUSD'] > 0],
        ['Code_economy', 'Code_partner'])
    # get product communities, partition
    # product_partition = get_louvain_partition(product_G)
    # product_partition, product_communities_orig = get_louvain_orig_partition(product_G)
    mod = -1
    for i in range(LRN):
        # total_partition = get_louvain_partition(total_G)
        tmp_product_partition, tmp_product_communities_orig = get_louvain_orig_partition(product_G)
        tmp_mod = nx.community.quality.modularity(product_G, tmp_product_communities_orig)
        # print('tmp modularity: ', tmp_mod)
        if mod < tmp_mod:
            mod = tmp_mod
            product_communities_orig = tmp_product_communities_orig
            product_partition = tmp_product_partition
    
    mod = -1
    for i in range(LRN):
        # total_partition = get_louvain_partition(total_G)
        tmp_total_partition, tmp_total_communities_orig = get_louvain_orig_partition(total_G)
        tmp_mod = nx.community.modularity(total_G, tmp_total_communities_orig)
        # print('tmp modularity: ', tmp_mod)
        if mod < tmp_mod:
            mod = tmp_mod
            total_communities_orig = tmp_total_communities_orig
            total_partition = tmp_total_partition

    fig = plot_communities_geo(product_partition, iso_corr,
                               'Telecommunication equipment', YEAR, show=SHOW)
    if WRITE:
        fig.write_image(images_root + f'tele_communities_{YEAR}.eps')
    fig = plot_communities_geo(total_partition, iso_corr,
                               'Total', YEAR, show=SHOW)
    if WRITE:
        fig.write_image(images_root + f'total_communities_{YEAR}.eps')

    # %%
    if YEAR == 2016:
        # get and preprocess DIST data
        # geos = pd.read_csv(csvs_root + 'geo_cepii.csv', keep_default_na=False)
        # %%
        # get distance between countries
        dist_inv = pd.read_csv(git_csvs_root + 'dist_inv.csv')
        dist_G = get_dist_network(dist_inv)
        ## get distance communities, partition
        # dist_partition = get_louvain_partition(dist_G)
        # dist_partition, dist_communities_orig = get_louvain_orig_partition(dist_G)
        mod = -1
        for i in range(LRN):
            # total_partition = get_louvain_partition(total_G)
            tmp_dist_partition, tmp_dist_communities_orig = get_louvain_orig_partition(dist_G)
            tmp_mod = nx.community.quality.modularity(dist_G, tmp_dist_communities_orig)
            # print('tmp modularity: ', tmp_mod)
            if mod < tmp_mod:
                mod = tmp_mod
                dist_communities_orig = tmp_dist_communities_orig
                dist_partition = tmp_dist_partition
        fig = plot_communities_geo(dist_partition, iso_corr,
                                   "Distance", show=SHOW)
        if WRITE:
            fig.write_image(images_root + 'dist_communities.eps')

        # load ALLIANCE data
        v4 = pd.read_csv(csvs_root + 'version41_csv/alliance_v41_by_member.csv')
        v4_to_products = pd.read_csv(git_csvs_root + 'v4_to_products.csv')
        v4_active_new = preprocess_alliances(v4, v4_to_products)
        alliance_lists = get_alliance_lists(v4_active_new, "Type I: Defense Pact")
        alliance_G = create_ally_network(alliance_lists, v4_active_new, weighted=True)
        # %% 
        # # get alliance communmities
        # alliance_partition = get_louvain_partition(ally_G)
        # alliance_partition, alliance_communities_orig = \
        #     get_louvain_orig_partition(ally_G)
        mod = -1
        for i in range(LRN):
            # total_partition = get_louvain_partition(total_G)
            tmp_alliance_partition, tmp_alliance_communities_orig = get_louvain_orig_partition(alliance_G)
            tmp_mod = nx.community.quality.modularity(alliance_G, tmp_alliance_communities_orig)
            # print('tmp modularity: ', tmp_mod)
            if mod < tmp_mod:
                mod = tmp_mod
                alliance_communities_orig = tmp_alliance_communities_orig
                alliance_partition = tmp_alliance_partition
        
        # add important countries that are not allied
        non_allied_countries = \
            ['HK', 'MO', 'TW', 'VN', 'SG', 'TH', 'SE', 'CH', 'ID']
        for i, country in enumerate(non_allied_countries):
            alliance_partition[country] = -i
        # %%
        fig = plot_communities_geo(alliance_partition, iso_corr,
                                   "Alliance", show=SHOW)
        if WRITE:
            fig.write_image(images_root + 'alliance_communities.eps')


    # %%
    # normalize each partitions
    excluded_countries_per_year = []
    all_countries = list(product_G.nodes())
    all_common_countries = []
    for country in all_countries:
        if country not in rta_year_partition.keys():
            # print(country, 'not in rta_year_partition')
            excluded_countries_per_year.append(country)
            pass
        elif country not in product_partition.keys():
            # print(country, 'not in product_partition')
            excluded_countries_per_year.append(country)
            pass
        elif country not in total_partition.keys():
            # print(country, 'not in total_partition')
            excluded_countries_per_year.append(country)
            pass
        elif country not in alliance_partition.keys():
            # # Hong Kong, Macao, Taiwan, Viet Nam, Singapore
            # # not in alliance_partition
            # # ==> add as sole communities
            # print(country, 'not in alliance_partition')
            excluded_countries_per_year.append(country)
            pass
        elif country not in dist_partition.keys():
            # print(country, 'not in dist_partition')
            excluded_countries_per_year.append(country)
            pass
        else:
            all_common_countries.append(country)
    excluded_countries.append(excluded_countries_per_year)

    # normalize rta_year_partition
    rta_year_partition_normalized = dict()
    product_partition_normalized = dict()
    total_partition_normalized = dict()
    dist_partition_normalized = dict()
    alliance_partition_normalized = dict()
    for country in all_common_countries:
        rta_year_partition_normalized[country] = rta_year_partition[country]
        product_partition_normalized[country] = product_partition[country]
        total_partition_normalized[country] = total_partition[country]
        dist_partition_normalized[country] = dist_partition[country]
        alliance_partition_normalized[country] = alliance_partition[country]

    # %%
    # compute NMI
    rta_year_partition_normalized_values = \
        list(rta_year_partition_normalized.values())
    product_partition_normalized_values = \
        list(product_partition_normalized.values())
    total_partition_normalized_values = \
        list(total_partition_normalized.values())
    dist_partition_normalized_values = \
        list(dist_partition_normalized.values())
    alliance_partition_normalized_values = \
        list(alliance_partition_normalized.values())

    product_v_rta = \
        NMI(product_partition_normalized_values, rta_year_partition_normalized_values)
    product_v_total = \
        NMI(product_partition_normalized_values, total_partition_normalized_values)
    product_v_dist = \
        NMI(product_partition_normalized_values, dist_partition_normalized_values)
    product_v_alliance = \
        NMI(product_partition_normalized_values, alliance_partition_normalized_values)
    print(f'NMI(product, rta) = {product_v_rta}')
    print(f'NMI(product, total) = {product_v_total}')
    print(f'NMI(product, dist) = {product_v_dist}')
    print(f'NMI(product, alliance) = {product_v_alliance}')
    NMI_product_v_rta.append(product_v_rta)
    NMI_product_v_total.append(product_v_total)
    NMI_product_v_dist.append(product_v_dist)
    NMI_product_v_alliance.append(product_v_alliance)

    total_v_rta = \
        NMI(total_partition_normalized_values, rta_year_partition_normalized_values)
    total_v_dist = \
        NMI(total_partition_normalized_values, dist_partition_normalized_values)
    total_v_alliance = \
        NMI(total_partition_normalized_values, alliance_partition_normalized_values)
    print(f'NMI(total, rta) = {total_v_rta}')
    print(f'NMI(total, dist) = {total_v_dist}')
    print(f'NMI(total, alliance) = {total_v_alliance}')
    NMI_total_v_rta.append(total_v_rta)
    NMI_total_v_dist.append(total_v_dist)
    NMI_total_v_alliance.append(total_v_alliance)

NMI_product_v_df = pd.DataFrame({
    'YEAR': pd.Series(YEARs, dtype='str'),
    'RTA': NMI_product_v_rta,
    'distance': NMI_product_v_dist,
    'alliance': NMI_product_v_alliance,
    'total': NMI_product_v_total})

NMI_total_v_df = pd.DataFrame({
    'YEAR': pd.Series(YEARs, dtype='str'),
    'RTA': NMI_total_v_rta,
    'distance': NMI_total_v_dist,
    'alliance': NMI_total_v_alliance})

fig = px.line(
    NMI_product_v_df,
    x='YEAR',
    y=['RTA', 'distance', 'alliance', 'total'],
    title='NMI between telecommunication and other networks',
    labels={'value': 'NMI'},
    markers=True,)
fig.update_layout(
    legend_title_text='Communities',)
if SHOW_NMI:
    fig.show()
if WRITE:
    fig.write_image(nmi_images_root + 'tele_v_others_1.eps')

fig = px.line(
    NMI_product_v_df.iloc[:4, :],
    x='YEAR',
    y=['RTA', 'distance', 'alliance', 'total'],
    title='NMI between telecommunication and other networks',
    labels={'value': 'NMI'},
    markers=True,)
fig.update_layout(
    legend_title_text='Communities',)
if SHOW_NMI:
    fig.show()
if WRITE:
    fig.write_image(nmi_images_root + 'tele_v_others_2.eps')

fig = px.line(
    NMI_total_v_df,
    x='YEAR',
    y=['RTA', 'distance', 'alliance'],
    title='NMI between total and other networks',
    labels={'value': 'NMI'},
    markers=True,)
fig.update_layout(
    legend_title_text='Communities',)
if SHOW_NMI:
    fig.show()
if WRITE:
    fig.write_image(nmi_images_root + 'total_v_others_1.eps')

fig = px.line(
    NMI_total_v_df.iloc[:4, :],
    x='YEAR',
    y=['RTA', 'distance', 'alliance'],
    title='NMI between total and other networks',
    labels={'value': 'NMI'},
    markers=True,)
fig.update_layout(
    legend_title_text='Communities',)
if SHOW_NMI:
    fig.show()
if WRITE:
    fig.write_image(nmi_images_root + 'total_v_others_2.eps')


# %%
# what are the friends of a country in each network?
# country = 'JP' 
# partner = 'CN'
country = False
if country:
    product_country_community = product_partition[country]
    product_country_friends = \
        [code for code in product_partition.keys() if \
            product_partition[code] == product_country_community]
    dist_country_community = dist_partition[country]
    dist_country_friends = \
        [code for code in dist_partition.keys() if \
            dist_partition[code] == dist_country_community]
    rta_country_community = rta_year_partition[country]
    rta_country_friends = \
        [code for code in rta_year_partition.keys() if \
            rta_year_partition[code] == rta_country_community]
    alliance_country_community = alliance_partition[country]
    alliance_country_friends = \
        [code for code in alliance_partition.keys() if \
            alliance_partition[code] == alliance_partition[country]]
    product_17_764_KUSD = products.query(
        'product=="764" and year==2017\
            and Code_economy==@country and Code_partner==@partner')['KUSD'].values[0]
    product_19_764_KUSD = products.query(
        'product=="764" and year==2019\
            and Code_economy==@country and Code_partner==@partner')['KUSD'].values[0]
    product_764_diff = product_19_764_KUSD - product_17_764_KUSD
    print(f"change in {country}'s imports from {partner}: {product_764_diff}")
    print(f'{country} product friends: {product_country_friends}')
    print(f'{country} dist friends: {dist_country_friends}')
    print(f'{country} rta friends: {rta_country_friends}')
    print(f'{country} alliance friends: {alliance_country_friends}')

