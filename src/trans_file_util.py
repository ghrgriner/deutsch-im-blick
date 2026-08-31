'''

'''

import pandas as pd
import re

#------------------------------------------------------------------------------
# Global variables
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Constants
#------------------------------------------------------------------------------
_PART_OF_SPEECH = ['Adjective','Adverb','Noun','Verb','Conjunction',
   'Contraction','Derived terms','Determiner','Interjection','Article',
   'Number','Numeral','Phrase','Prefix','Preposition','Prepositional phrase',
   'Pronoun','Proper noun','Suffix','Particle','Punctuation mark','Postposition',
   'Proverb','Interfix']

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def get_token2(x):
    '''Get second token from line using '|' or '}' as delimiters.

    The purpose is the input is a line containing a `trans-top` or similar
    (Wikitext) template, so the first token is the template name and the
    second token is the first template parameter which we want to extract
    (because this parameter gives a summary of the definition being
    translated).
    Example inputs: '{{trans-top|unit of currency}}'
                    '{{trans-top-see|meaningless words|gibberish}}'
    '''

    if pd.isna(x):
        return ''
    elif '|' not in x:
        return ''
    else:
        x_nocmt = re.sub(r'<!--.*?-->','',x)
        x_list = re.split(r'\||\}', x_nocmt)
        #print(x_list)
        return x_list[1]

def add_pseq(df):
    df['seq_on_page'] = df.groupby(['page']).cumcount() + 1

def add_tseq(df):
    df['seq_in_param1'] = df.groupby(['page','tt_param1']).cumcount() + 1

def strip_bullet1(x):
    return _strip_bullet(x, '* ')

def strip_bullet2(x):
    return _strip_bullet(x, '*: ')

def strip_bullet3(x):
    return _strip_bullet(x, '*:: ')

def _strip_bullet(x, pfx):
    if not x:
        return ''
    if x.startswith(pfx):
        return x[len(pfx):]
    else:
        raise ValueError('ERROR: should be empty or start with prefix? '
                         f'{x=}, {pfx=}')

def _get_pos(h3, h4, h5):
    if h3 in _PART_OF_SPEECH: return h3
    if h4 in _PART_OF_SPEECH: return h4
    if h5 in _PART_OF_SPEECH: return h5
    return ''

def add_enwk_part_of_speech(df):
    df['enwk_part_of_speech'] = [
      _get_pos(h3, h4, h5) for h3, h4, h5 in df[['h3','h4','h5']].values
                                ]
