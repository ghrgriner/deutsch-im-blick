'''Extract page revisions from translations
'''

import pandas as pd
import csv

#------------------------------------------------------------------------------
# Parameters
#------------------------------------------------------------------------------
LONG_TRANS_FILE = '../output/intermediate/en_long_trans.txt'
LONG_PAGE_FILE = '../output/intermediate/en_long_pages.txt'
OUTPUT_FILE = '../output/translations/tr_revisions.txt'

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Main Entry Point
#------------------------------------------------------------------------------

tdf = pd.read_csv(LONG_TRANS_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                  na_filter=False)
pdf = pd.read_csv(LONG_PAGE_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                  na_filter=False)
tkdf = tdf[tdf.has_trans == 'Y'][['page']].drop_duplicates()
rdf = pdf.merge(tkdf, how='inner', on='page')
rdf[['revision']].to_csv(OUTPUT_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                         index=False)
