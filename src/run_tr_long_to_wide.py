'''Convert translations from 'long' to 'wide' format and subset languages
'''

import csv
import warnings

import pandas as pd
import numpy as np
from trans_file_util import strip_bullet1, strip_bullet2, strip_bullet3

#-----------------------------------------------------------------------------
# Parameters
#-----------------------------------------------------------------------------
INPUT_TRANS_FILE = '../output/intermediate/en_long_trans.txt'
INPUT_LANG_FILE = '../input/lang_names_to_code.txt'
OUTPUT_FILE = '../output/intermediate/en_sel_wide_trans.txt'
#DESC_TO_CODE_DICT = {}
PIVOT_KEY = ['eeseq','page','tteseq','h3','h4','h5','transtop_line']

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------
#def lev12_to_code(level1, level2, level3):
#    if (not pd.isna(level3)) and level3 != '':
#        return ''
#
#    if not level2:
#        return DESC_TO_CODE_DICT.get(level1 + ':', '')
#    else:
#        return DESC_TO_CODE_DICT.get(level2 + ':', '')

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
warnings.simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

df = pd.read_csv(INPUT_TRANS_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                 na_filter=False)
df['tteseq'] = np.where(df.tteseq == '', '9999999', df.tteseq)
df['tteseq'] = df.tteseq.astype(int)

#for lang_code, lang_desc in LANGUAGES:
#    if lang_code in DESC_TO_CODE_DICT:
#        raise ValueError(f'{lang_desc} already exists!')
#    DESC_TO_CODE_DICT[lang_desc] = lang_code

#df['lang_code'] = [ lev12_to_code(level1, level2, level3)
#                              for level1, level2, level3
#                in df[['lang_name_b1','lang_name_b2','lang_name_b3']].values ]
ldf = pd.read_csv(INPUT_LANG_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                  na_filter=False)
LANGUAGES = [ (item, '') for item in ldf.lang_code.unique().tolist() ]
df['lang_name1'] = df.lang_name_b1.map(strip_bullet1)
df['lang_name2'] = df.lang_name_b2.map(strip_bullet2)
df['lang_name3'] = df.lang_name_b3.map(strip_bullet3)

df = df.merge(ldf, on=['lang_name1','lang_name2','lang_name3'], how='left')
df['lang_code'] = df.lang_code.fillna('')

#df = df.drop(['lang_name_b1','lang_name_b2','lang_name_b3'], axis=1)

df['count_line'] = [ countit(level2, level3, trans)
                         for level2, level3, trans
                in df[['lang_name_b2','lang_name_b3','trans']].values ]
df['trans_count'] = df.groupby(PIVOT_KEY)['count_line'].transform('sum')
df['trans_count'] = df['trans_count'].fillna(0)

print(df)
print(df.columns)

df_nodups = df[~df[PIVOT_KEY + ['lang_code']].duplicated(keep='last')]

df_wide = df_nodups.pivot(index=PIVOT_KEY + ['trans_count'],
                          columns='lang_code', values='trans'
                         ).add_prefix('tr_enwk_')
df_wide = df_wide.reset_index()

tr_order = [ 'tr_enwk_' + code for code, _ in LANGUAGES ]
for var in tr_order:
    if var not in df_wide:
        df_wide[var] = ''

new_order = (['page','h3','h4','h5','tteseq','transtop_line']
             + tr_order + ['trans_count'])
dups = df_wide.duplicated(['page','tteseq'])
if dups.any():
    print(df_wide[df_wide.dups][['page','tteseq','transtop_line']])
    raise ValueError('df_wide has duplicates by page+tteseq!')

df_wide = df_wide[new_order]

print(df_wide)

df_wide.to_csv(OUTPUT_FILE, sep='\t', quoting=csv.QUOTE_NONE, index=False)
