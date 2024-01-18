import pandas as pd
import numpy as np
from thefuzz import fuzz

# not sure if this is necessary
def find_fuzz(rta_df, country, column='RTA Name'):
    fuzz_scores = rta_df[column].apply(lambda x: fuzz.partial_ratio(x, country))
    return rta_df[fuzz_scores > 80]

