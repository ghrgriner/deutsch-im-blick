'''Convert translations from 'long' to 'wide' format and subset languages

This gives the same output as `run_tr_long_to_wide.py`.

The run time is a little longer (104s vs 93s), but the memory use is much
lower. The other program tops out at 12g resident memory and 13g virtual.
'''

import csv
import warnings
from dataclasses import make_dataclass, field

import pandas as pd
import numpy as np
from trans_file_util import (
    strip_bullet1, strip_bullet2, strip_bullet3,
    _get_pos,
                            )
# This dataclass is the output record, w/o the language fields
WideRec = make_dataclass('WideRec', [
    ('page',  str, field(default='')),
    ('h3',  str, field(default='')),
    ('h4',  str, field(default='')),
    ('h5',  str, field(default='')),
    ('enwk_part_of_speech',  str, field(default='')),
    ('tteseq',  str, field(default='')),
    ('transtop_line', str, field(default='')),
    ('trans_count', int, field(default=0)),
    ])

#-----------------------------------------------------------------------------
# Parameters
#-----------------------------------------------------------------------------
NROWS = None # rows to use from INPUT_TRANS_FILE, None uses all
INPUT_TRANS_FILE = '../output/intermediate/en_long_trans.txt'
INPUT_LANG_FILE = '../input/lang_names_to_code.txt'
OUTPUT_FILE = '../output/intermediate/en_sel_wide_trans.txt'

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

def write_entry(otf_writer, trec):
    data = ([trec.page, trec.tteseq, trec.h3, trec.h4, trec.h5,
             trec.enwk_part_of_speech, trec.transtop_line,
             str(trec.trans_count)]
            + [ str(item) for item in trec.transd.values() ]
           )
    for item in data:
        if '\t' in item or '\r' in item or '\n' in item:
            print(f'BAD CHAR in {trec.page=}, {item=}')
    clean_data = [ item.replace('\t',' ').replace('\r',' ').replace('\n',' ')
                   for item in data ]
    otf_writer.writerow(clean_data)

def process_entry(otf_writer, ldict_, row_list, lang_codes_):
    trec = WideRec()
    for row_idx, erow in enumerate(row_list):
        if row_idx == 0:
            trec.page = erow['page']
            trec.h3 = erow['h3']
            trec.h4 = erow['h4']
            trec.h5 = erow['h5']
            tteseq = erow['tteseq']
            trec.tteseq = '9999999' if tteseq == '' else tteseq
            trec.transtop_line = erow['transtop_line']
            trec.trans_count = 0
            trec.transd = { key: '' for key in lang_codes_ }
            trec.enwk_part_of_speech = _get_pos(trec.h3, trec.h4, trec.h5)

        if countit(erow['lang_name_b2'], erow['lang_name_b3'], erow['trans']):
            trec.trans_count = trec.trans_count + 1
        lang_name1 = strip_bullet1(erow['lang_name_b1'])
        lang_name2 = strip_bullet2(erow['lang_name_b2'])
        lang_name3 = strip_bullet3(erow['lang_name_b3'])
        key = (lang_name1, lang_name2, lang_name3)
        lang_code = ldict_['lang_code'].get(key, '')
        if lang_code != '':
            trec.transd[lang_code] = erow['trans']
    write_entry(otf_writer, trec)

#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

with (open(INPUT_TRANS_FILE, mode='r', newline='', encoding='utf-8') as itf,
      open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as otf):

    ldf = pd.read_csv(INPUT_LANG_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                  na_filter=False)
    ldf = ldf.set_index(LANG_NAMES)
    ldict = ldf.to_dict()
    lang_codes = sorted(set(list(ldict['lang_code'].values())))
    reader = csv.DictReader(itf, delimiter='\t', quoting=csv.QUOTE_NONE)

    writer = csv.writer(otf, delimiter='\t',
                        quoting=csv.QUOTE_NONE,
                        quotechar=None,
                        lineterminator='\n')
    writer.writerow(['page','tteseq','h3','h4','h5','enwk_part_of_speech',
                     'transtop_line','trans_count']
        + [ 'tr_enwk_' + item for item in lang_codes ]
                   )

    row_counter = 0
    curr_entry = []
    for row in reader:
        if NROWS is not None and row_counter >= NROWS:
            break
        if row_counter % 100000 == 0:
            pass
            #print(f'{row_counter=}')
        row_counter = row_counter + 1
        if (curr_entry
            and (row['page'] == curr_entry[-1]['page'])
            and (row['tteseq'] == curr_entry[-1]['tteseq'])):
            curr_entry.append(row)
        elif curr_entry:
            process_entry(writer, ldict, curr_entry, lang_codes)
            curr_entry = [row]
        else:
            # curr_entry = [] only on first row read
            curr_entry.append(row)
    process_entry(writer, ldict, curr_entry, lang_codes)
