'''Get summary statistics and detailed (by-note) info for translations

This creates four output files. Files for public sharing are output to the
`../output/translations` directory. We also create files in
`../output/intermediate/` that we do not share (upload to the repo).
Users can obtain these latter files by running this program themselves.

1. TRANS_AVAIL_FILE (public): for each note in the Deutsch im Blick deck
and language, give indicator whether translation is available.

2. TRANS_LANG_SENSE_FILE (not public): add translation and a couple other
fields (i.e., count of translations in all (most) languages and full line
with the template for the header of the translation table).

3. TRANS_STATS_FILE (public): summary completion information by language.
This is a tab-delimited file. It's similar information to the results
table in the wiki.

4. MD_ROW_FILE (not public): this is basically the same as the previous
item, but the rows of the table are in GitHub markdown format for pasting
into the wiki.

5. This is not an output file, but the first table in the Results page of
the wiki is from the last sets of `value_counts` printed to stdout.
'''

import pandas as pd
import csv

from trans_file_util import get_token2, add_tseq

#------------------------------------------------------------------------------
# Parameters
#------------------------------------------------------------------------------
NROWS = None # rows to use from ENWK_TRANS_FILE

ENWK_TRANS_FILE = '../output/intermediate/en_sel_wide_trans.txt'
INPUT_LANG_FILE = '../input/lang_names_to_code.txt'
DECK_FILE = '../output/deck/dib_deck.txt'
DECK_FIELDS_FILE = '../output/deck/dib_deck_fields.txt'
TRANS_AVAIL_FILE = '../output/translations/tr_avail_by_note_dib.txt'
TRANS_AVAIL_VARS = ['word_id', 'note_class', 'page','enwk_part_of_speech',
                    'tt_param1', 'seq_in_param1', 'seq_of_ref', 'lang',
                    'lang_desc', 'has_trans']
TRANS_LANG_SENSE_FILE = '../output/intermediate/tr_lang_sense_dib.txt'
TRANS_LS_ADDL_VARS = ['trans_count','transtop_line','translation']

TRANS_STATS_FILE = '../output/translations/tr_stats_dib.txt'
TRANS_STATS_VARS = ['lang','lang_desc','denom','num','pct100str','pct100']
MD_ROW_FILE = '../output/intermediate/tr_stats_dib_md.txt'
TR_ATTR_FILE = '../output/intermediate/tr_attrition_md.txt'

TR_ATTR_ROWS = [
 ('_NOPAGESOP', 'No Wiktionary page - phrase is sum-of-parts'),
 ('_NOPAGE', 'No Wiktionary page - phrase is not sum-of-parts'),
 ('_NOTRANS', 'Page exists but no translation table [a]'),
 ('_NOSENSESOP', 'Translations available but no matching sense and '
                 'sense is sum-of-parts [b]'),
 ('_NOSENSE', 'Translations available but no matching sense and sense'
              ' is not sum-of-parts [b]'),
 ('_UNEXNM',  'Matching or partially matching sense expected but none'
              ' available [c]'),
 ('LINK', 'Matching or partially matching sense available'),
]

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def has_trans(x):
    if not x or 't-needed' in x:
        return False
    else:
        return True

def dupkey(df_, vars_, error=True):
    probs = df_.duplicated(subset=vars_, keep=False)
    if probs.any():
        print(df_[probs].sort_values(vars_))
        if error:
            raise ValueError(f'Duplicates in data frame by {vars_=}')
        else:
            print(f'WARNING: Duplicates in data frame by {vars_=}')

def calc_has_trans_freq(group):
    return calc_freq(group, 'has_trans')

def calc_freq(group, var):
    denom = len(group[ ~pd.isna(group[var]) ])
    num = sum(group[var])
    pct100 = num * 100 / denom
    pct100str = f'{pct100:.1f}'
    return pd.Series({'denom': denom, 'num': num,
                     'pct100': pct100, 'pct100str': pct100str})

def get_indices_to_drop(pages_to_keep):
    page_df = pd.read_csv(ENWK_TRANS_FILE, sep='\t',
                   quoting=csv.QUOTE_MINIMAL, usecols=['page'], nrows=NROWS,
                   na_filter=False)
    page_df['keep_page'] = page_df.page.map(lambda x: x in pages_to_keep)
    page_df = page_df.reset_index()

    # Use `item + 1` b/c page_df.index has first data row with index 0, but
    # `skiprows` parameter will give header row index 0
    skip_indices = {
             item + 1
             for item in page_df[~page_df.keep_page]['index'].tolist()
                   }
    return skip_indices

def print_attrition(attr_file, vocab_deck, tkdf_, sm_word_ids):
    # Identify unexnm (unexpected not-matched) words in list. `
    for_unexnm = tkdf_.merge(sm_word_ids, how='right', on='word_id',
                             indicator='prob')
    unexnm = for_unexnm[for_unexnm.prob == 'right_only']

    vocab_deck['avail'] = vocab_deck.enwk_def.map(
                lambda x: x if x.startswith('_') else 'LINK')
    vocab_deck.loc[vocab_deck.word_id.isin(unexnm.word_id),'avail'] = '_UNEXNM'

    n = vocab_deck.avail.value_counts()
    pct = vocab_deck.avail.value_counts(normalize=True)
    tbl = pd.DataFrame(TR_ATTR_ROWS, columns=['avail','label'])
    tbl = tbl.set_index('avail')
    tbl['cnt'] = n
    tbl['cnt'] = tbl.cnt.fillna(0).astype(int)
    tbl['proportion'] = pct
    tbl['proportion'] = tbl.proportion.fillna(0)
    tbl = tbl.reset_index()
    rank_dict = { code: idx for idx, (code, _) in enumerate(TR_ATTR_ROWS) }
    tbl['rank'] = tbl.avail.map(lambda x: rank_dict[x])
    tbl = tbl.sort_values(['rank'])
    #tbl['label'] = tbl.avail.map(lambda x: label_dict[x])
    tbl['pct100str'] = tbl.proportion.map(lambda x: str(round(x*100, 1)))
    tbl['md_row'] = ('| ' + tbl.label + ' | ' + tbl.cnt.astype(str) +
                    ' | ' + tbl.pct100str + ' |')
    tbl[['md_row']].to_csv(attr_file, sep='\t', quoting=csv.QUOTE_NONE,
                           index=False)
    print(tbl[['label','cnt','pct100str']])

#------------------------------------------------------------------------------
# Main Entry Point
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# 1. Get the language file, because we will use the 'wide' translation file
#    which identifies languages by code but not description.
#------------------------------------------------------------------------------
ldf = pd.read_csv(INPUT_LANG_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                  na_filter=False)
LANG_DICT = { cod: dsc for cod, dsc in ldf[['lang_code','lang_desc']].values }

f_df = pd.read_csv(DECK_FIELDS_FILE, sep='|', quoting=csv.QUOTE_NONE,
                 na_filter=False, names=['Columns'])
columns = f_df.iloc[0, 0].split('\t')
#print(f_df)

#------------------------------------------------------------------------------
# 2. Get the Deutsch im Blick vocabular deck, which we refer to as the
# 'source deck'. The `enwk_def` field may contain more than one Wiktionary
# page+gloss identifier, so the data frame is # 'exploded' on this list
# after delimiting by '|'.
#------------------------------------------------------------------------------
df = pd.read_csv(DECK_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                 usecols=['word_id','note_class','enwk_def'],
                 na_filter=False, names=columns)
deck_copy = df.copy()
should_match_word_ids = df[~df.enwk_def.str.startswith('_')][['word_id']]
df = df.fillna('')
df['enwk_def_list'] = df.enwk_def.map(
    lambda x: [item.strip() for item in x.split('|')] if x else [])
print(df)
x_df = df.explode('enwk_def_list').rename(
    columns={'enwk_def_list': 'enwk_def_1tok'})
x_df['seq_of_ref'] = x_df.groupby('word_id').cumcount() + 1
print(x_df)

res = x_df.enwk_def_1tok.map(
   lambda x: x.split(':', maxsplit=2) if not x.startswith('_') else ('','',''))
x_df['page'] = [ item[0] for item in res ]
x_df['qual'] = [ item[1] for item in res ]
x_df['tt_param1'] = [ item[2] for item in res ]

#------------------------------------------------------------------------------
# 3. Read (wide) translation file, keeping only pages identified in the source
# deck data frame above.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# The wide file has many records we don't need and many variables, so we can
# save a significant amount of time by reading the file twice. First we read
# only the `page` column to get the row indices of the transtab entries on
# the Wiktionary pages we want, and then a second time to get all variables
# but skipping most rows. This reduces runtime from 2.5 to 1 minute (for the
# whole program). Memory consumption is greatly reduced as well. Before the
# fix res M was around 13 g and up to 25 g virtual. Now, res M tops around
# 5 g with negligible virtual use.
#------------------------------------------------------------------------------
indices_to_drop = get_indices_to_drop(pages_to_keep=set(x_df.page.tolist()))

#-----------------------------------------------------------------------------
# 4. Merge translations and (exploded) source deck data frames. Limit to
# matching page and translation table entry gloss.
#-----------------------------------------------------------------------------
t_df = pd.read_csv(ENWK_TRANS_FILE, sep='\t', quoting=csv.QUOTE_MINIMAL,
                   nrows=NROWS,
                   skiprows=lambda x: x in indices_to_drop,
                   na_filter=False)
t_df['tt_param1'] = t_df.transtop_line.map(get_token2)
add_tseq(t_df)
print(t_df)

tk_df = t_df.merge(
    x_df[['word_id','note_class','page','tt_param1','seq_of_ref']],
    how='inner', on=['page','tt_param1'], indicator=True)
print('\nPrinting tk_df')
print(tk_df)

dupkey(df_=tk_df, vars_=['word_id','page','tt_param1',
                        'seq_in_param1','seq_of_ref'])

#------------------------------------------------------------------------------
# 5. Transform translation set from wide to long.
#------------------------------------------------------------------------------
tk_long = pd.wide_to_long(tk_df, stubnames='tr_enwk_',
            i=['word_id','page','tt_param1','seq_in_param1','seq_of_ref'],
            j='lang', suffix=r'\D+')
tk_long = tk_long.reset_index()
tk_long['has_trans'] = tk_long.tr_enwk_.map(has_trans)
tk_long['has_trans_YN'] = tk_long.has_trans.map(lambda x: 'Y' if x else 'N')
tk_long['lang_desc'] = tk_long.lang.map(lambda x: LANG_DICT[x])
tk_long['t_lang'] = 't_' + tk_long.lang
tk_long.rename(columns = {'tr_enwk_': 'translation'}, inplace=True)
print('\nPrinting tk_long')
print(tk_long)

tk_long[TRANS_AVAIL_VARS + TRANS_LS_ADDL_VARS].to_csv(
    TRANS_LANG_SENSE_FILE, sep='\t', quoting=csv.QUOTE_NONE, index=False)

#------------------------------------------------------------------------------
# 6. We already have a wide data frame, but pivoting back only loses
# a bit of time and the code is cleaner (compare to commented-out below)
# so we will use `pivot`.
#------------------------------------------------------------------------------
tk_wide = tk_long.pivot(index=['word_id','note_class','page',
               'enwk_part_of_speech','tt_param1','seq_in_param1','seq_of_ref'],
                        columns = 't_lang',
                        values = 'has_trans_YN').sort_values(['word_id'])
print(tk_wide)
tk_wide.to_csv(TRANS_AVAIL_FILE, sep='\t', quoting=csv.QUOTE_NONE)

#------------------------------------------------------------------------------
# 7. Now, need data frame, one record per word_id x lang, restricted to
#   word_ids where `enwk_def` does not start with '_' with indicator whether
#   all `word_id` records are True
#------------------------------------------------------------------------------
tk_for_summ = tk_long[tk_long.note_class == 'C'].groupby(
       ['word_id','note_class','lang'])['has_trans'].agg(all).reset_index()
print(tk_for_summ)

final_df = tk_for_summ.groupby('lang').apply(calc_has_trans_freq,
                                             include_groups=False)
final_df = final_df.sort_values(by='pct100', ascending=False)
final_df.reset_index(inplace=True)
final_df['lang_desc'] = final_df.lang.map(lambda x: LANG_DICT[x])
print(final_df)
final_df[TRANS_STATS_VARS].to_csv(TRANS_STATS_FILE, sep='\t',
                                  quoting=csv.QUOTE_NONE, index=False)

final_df['md_row'] = ('| ' + final_df.lang + ' | ' + final_df.lang_desc +
         ' | ' + final_df.num.astype(str) + ' | ' + final_df.pct100str + ' |')
final_df['md_row'].to_csv(MD_ROW_FILE, sep='\t',
                          quoting=csv.QUOTE_NONE, index=False)

#-----------------------------------------------------------------------------
# 8. 'Attrition' counts for source deck. That is, give number of entries
# included in translation completion analysis and reason excluded.
#-----------------------------------------------------------------------------
print(deck_copy.note_class.value_counts())
print_attrition(attr_file=TR_ATTR_FILE,
                vocab_deck=deck_copy[deck_copy.note_class == 'C'].copy(),
                tkdf_=tk_df, sm_word_ids=should_match_word_ids)

