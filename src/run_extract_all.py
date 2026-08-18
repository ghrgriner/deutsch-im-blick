#   Extract almost all translations from English Wiktionary
#   Copyright (C) 2026 Ray Griner (rgriner_fwd@outlook.com)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#------------------------------------------------------------------------------

'''Extract almost all translations from English Wiktionary

See `all_languages.py` docstring for why this is 'almost all' and not 'all'.

See `extract_enwk_trans` docstring for extraction details.
'''

from all_languages import LANGUAGES
from extract_enwk_trans import extract_enwk_trans

#-----------------------------------------------------------------------------
# Parameters
#-----------------------------------------------------------------------------
# This file isn't uploaded to the repository.
# Dump or file export from Wikimedia. See `extract_enwk_trans` docstring for
# considerations.
INPUT_FILE = ('../input/enwk/'
              'enwiktionary-20260701-pages-articles-multistream.xml.bz2')
MAX_PAGES = None # int or None (no maximum)

OUT_TRANS_FILE = '../output/intermediate/en_all_trans.txt'
OUT_PAGE_FILE = '../output/intermediate/en_all_pages.txt'

#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------
extract_enwk_trans(input_file=INPUT_FILE,
                   max_pages=MAX_PAGES,
                   languages=LANGUAGES,
                   output_trans_file=OUT_TRANS_FILE,
                   output_page_file=OUT_PAGE_FILE)
