'''Convert translations from 'long' to 'wide' format and subset languages
'''

import csv
import warnings

import pandas as pd
import numpy as np
from trans_file_util import (
    strip_bullet1, strip_bullet2, strip_bullet3,
    add_enwk_part_of_speech,
                            )

#-----------------------------------------------------------------------------
# Parameters
#-----------------------------------------------------------------------------
NROWS = None # rows to use from INPUT_TRANS_FILE, None uses all
INPUT_TRANS_FILE = '../output/intermediate/en_long_trans.txt'
INPUT_LANG_FILE = '../input/lang_names_to_code.txt'
OUTPUT_FILE = '../output/intermediate/en_sel_wide_trans.txt'
PIVOT_KEY = ['eeseq','page','tteseq','h3','h4','h5','transtop_line']

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------
LANG_NAMES = ['lang_name1','lang_name2','lang_name3']

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------
def countit(level2, level3, trans):
    if level2: return 0
    if level3: return 0
    if not trans: return 0
    if 't-needed' in trans: return 0
    return 1

#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

# Suppress the pandas fragmentation performance warning
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

df = pd.read_csv(INPUT_TRANS_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                 nrows=NROWS, na_filter=False)
df['tteseq'] = np.where(df.tteseq == '', '9999999', df.tteseq)
df['tteseq'] = df.tteseq.astype(int)

df['lang_name1'] = df.lang_name_b1.map(strip_bullet1)
df['lang_name2'] = df.lang_name_b2.map(strip_bullet2)
df['lang_name3'] = df.lang_name_b3.map(strip_bullet3)

ldf = pd.read_csv(INPUT_LANG_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                  na_filter=False)
df = df.merge(ldf[ LANG_NAMES + ['lang_code']], on=LANG_NAMES, how='left')
df['lang_code'] = df.lang_code.fillna('')

df['count_line'] = [ countit(level2, level3, trans)
                         for level2, level3, trans
                in df[['lang_name_b2','lang_name_b3','trans']].values ]
df['trans_count'] = df.groupby(PIVOT_KEY)['count_line'].transform('sum')
df['trans_count'] = df['trans_count'].fillna(0)

df = df.drop(['lang_name_b1','lang_name_b2','lang_name_b3'], axis=1)

print(df)

df_nodups = df[~df[PIVOT_KEY + ['lang_code']].duplicated(keep='last')]

df_wide = df_nodups.pivot(index=PIVOT_KEY + ['trans_count'],
                          columns='lang_code', values='trans'
                         ).add_prefix('tr_enwk_')
df_wide = df_wide.reset_index()
add_enwk_part_of_speech(df_wide)

tr_order = [ 'tr_enwk_' + code for code in ldf.lang_code.unique().tolist() ]
for var in tr_order:
    # on full data, all vars should be present, so no need for sparse data type
    if var not in df_wide:
        df_wide[var] = ''

new_order = (['page','tteseq','h3','h4','h5','enwk_part_of_speech',
              'transtop_line','trans_count'] + sorted(tr_order))
dups = df_wide.duplicated(['page','tteseq'])
if dups.any():
    print(df_wide[df_wide.dups][['page','tteseq','transtop_line']])
    raise ValueError('df_wide has duplicates by page+tteseq!')

df_wide = df_wide[new_order]

print(df_wide)

df_wide.to_csv(OUTPUT_FILE, sep='\t', quoting=csv.QUOTE_NONE, index=False)
