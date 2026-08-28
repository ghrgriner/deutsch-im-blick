#   Extract all translations from English Wiktionary
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

'''Extract all translations from English Wiktionary in long format

See `extract_enwk_tr_long` docstring for extraction details.
'''

from extract_enwk_tr_long import extract_enwk_tr_long

#-----------------------------------------------------------------------------
# Parameters
#-----------------------------------------------------------------------------
# This file isn't uploaded to the repository.
# Dump or file export from Wikimedia. See `extract_enwk_trans` docstring for
# considerations.
INPUT_FILE = ('../input/enwk/'
              'enwiktionary-20260701-pages-articles-multistream.xml.bz2')
MAX_PAGES = None # int or None (no maximum)

OUT_TRANS_FILE = '../output/intermediate/en_long_trans.txt'
OUT_PAGE_FILE = '../output/intermediate/en_long_pages.txt'

#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------
extract_enwk_tr_long(input_file=INPUT_FILE,
                   max_pages=MAX_PAGES,
                   output_trans_file=OUT_TRANS_FILE,
                   output_page_file=OUT_PAGE_FILE)
