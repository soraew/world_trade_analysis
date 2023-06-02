import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
from tqdm import tqdm



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
    


df = pd.read_csv(
    'output/china_usa_trade/chunks/6_1_china_us_filtered.csv',
    converters={
        'Partner': lambda s: replace_0(s),
        'US dollars at current prices in thousands Footnote':\
        lambda s: replace_Estimated(s),
        }
    )

df_gp_year = df[['year', 'economy_label', 'KUSD']]
df_gp_year = df_gp_year.groupby(['year', 'economy_label']).sum()

china = df_gp_year.loc[(slice(None), 'China'), :]

usa = df_gp_year.loc[(slice(None), 'United States of America'), :]

plt.plot(china.index.get_level_values(0), china['KUSD'], label='China')
plt.show()




breakpoint()
