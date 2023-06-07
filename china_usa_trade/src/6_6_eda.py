import pandas as pd

import numpy as np
import matplotlib.pyplot as plt

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
    


# Read in the data
df = pd.read_csv(
    'csvs/6_6_xaa_filtered.csv',
    converters={
        'partner': lambda s: replace_0(s),
        'KUSD_footnote':\
        lambda s: replace_Estimated(s),
        }
)
country_df = pd.read_csv('../../data/trade/BACI/countries.csv')
year_range = df.year.unique()


# prepare data
df_china = df[df.economy_label=="China"]
df_china = df_china[["year", "economy_label", "partner_label", "flow_label", "KUSD"]]

countries = country_df.Name.values
countries = np.append(
    countries,
    [
        "United States of America", 
        "China, Hong Kong SAR", 
        "China, Taiwan Province of",
        "Türkiye",
        "Iran (Islamic Republic of)",
        "Czechia",
        "Switzerland, Liechtenstein",
        "China, Macao SAR",
        "Korea, Dem. People's Rep. of",
        "Venezuela (Bolivarian Rep. of)",
        "Côte d'Ivoire",
        "Congo, Dem. Rep. of the",
        "Lao People's Dem. Rep.",
        "Bolivia (Plurinational State of)",
        "North Macedonia",
        "Curaçao",
        "State of Palestine",
        "Cabo Verde",
        "Eswatini",
        "British Virgin Islands",
        "Micronesia (Federated States of)",
        "Wallis and Futuna Islands",
        "Holy See",
    ]
    )

# top 10 export partners per year
df_china_partners = df_china[df_china.flow_label=="Exports"]

df_china_partners = \
    df_china_partners\
    .groupby(["year", "partner_label"])\
    .sum(numeric_only=True)\
    .reset_index()
df_china_partners = \
    df_china_partners\
    .sort_values(by=["year", "KUSD"], ascending=False)

df_china_partners["rank"] = \
    df_china_partners\
    .groupby("year")["KUSD"].rank("dense", ascending=False)
df_china_partners = df_china_partners.reset_index(drop=True)

df_china_partners_countries = df_china_partners[df_china_partners.partner_label.isin(countries)]
df_china_partners_countries = df_china_partners_countries.reset_index(drop=True)


# write top 400 export partners per year to text file
for year in year_range:
    df_china_partners_countries_year = \
        df_china_partners_countries\
        [df_china_partners_countries.year==year]
    arr_china_partners_countries_year = \
        df_china_partners_countries_year\
        [df_china_partners_countries_year["rank"]<=400]\
        .partner_label.values
    # write to text file named after year
    np.savetxt(
        "csvs/6_6_top_400_export_partner_countries_{}.txt".format(year),
        arr_china_partners_countries_year,
        fmt="%s"
    )


    df_china_partners_year = \
        df_china_partners\
        [df_china_partners.year==year]
    arr_china_partners_year = \
        df_china_partners_year\
        [df_china_partners_year["rank"]<=400]\
        .partner_label.values
    # write to text file named after year
    np.savetxt(
        "csvs/6_6_top_400_export_partners_{}.txt".format(year),
        arr_china_partners_year,
        fmt="%s"
    )




