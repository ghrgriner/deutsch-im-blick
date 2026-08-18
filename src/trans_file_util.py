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
