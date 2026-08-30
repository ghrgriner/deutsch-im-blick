#   Extract translations for selected languages from English Wiktionary
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

'''Extract translations for selected languages from English Wiktionary

See `extract_enwk_trans` docstring below for details.
'''

import bz2
import xml.etree.ElementTree as ET

from collections import Counter
from dataclasses import make_dataclass, field

import csv
import re

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------
# This should probably be extracted programmatically, but we just hardcode it
XMLNS = '{http://www.mediawiki.org/xml/export-0.11/}'

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
PageInfo = make_dataclass('PageInfo', [
    ('revision',  str, field(default='')),
    ('timestamp', str, field(default='')),
    ('wikitext',  str, field(default='')),
                                      ])
TransRec = make_dataclass('TransRec', [
    ('title',  str, field(default='')),
    ('eeseq',  str, field(default='0')),
    ('tteseq', str, field(default='0')),
    ('transtop_line', str, field(default='')),
    ('h3',  str, field(default='')),
    ('h4',  str, field(default='')),
    ('h5',  str, field(default='')),
    ('lev1',  str, field(default='')),
    ('lev2',  str, field(default='')),
    ('lev3',  str, field(default='')),
    ('has_trans',  bool, field(default='')),
    ('trans',  bool, field(default='')),
                                      ])
#-----------------------------------------------------------------------------
# Private Functions
#-----------------------------------------------------------------------------
def _update_word_from_xml_dump(word, elem):
    revision_elem = elem.find(f'{XMLNS}revision')
    word.revision = int(revision_elem.find(f'{XMLNS}id').text)
    word.timestamp = revision_elem.find(f'{XMLNS}timestamp').text
    word.wikitext = revision_elem.find(f'{XMLNS}text').text

def writerow(otf_writer, trec):
    has_transYN = 'Y' if trec.has_trans else 'N'
    data = ([trec.title, trec.eeseq, trec.tteseq, trec.transtop_line, trec.h3,
             trec.h4, trec.h5, trec.lev1, trec.lev2, trec.lev3, has_transYN,
             trec.trans.strip()])
    for item in data:
        if '\t' in item or '\r' in item or '\n' in item:
            print(f'BAD CHAR in {trec.title=}, {item=}')
    clean_data = [ item.replace('\t',' ').replace('\r',' ').replace('\n',' ')
                   for item in data ]
    otf_writer.writerow(clean_data)

def split_line(line, which_colon):
    #line_list = line.split(':', maxsplit=which_colon + 1)
    line_list = line.split(':', maxsplit=which_colon)
    if len(line_list) < which_colon + 1:
        #print(line)
        return False, None, None

    #print(line_list[0:which_colon])
    return True, ':'.join(line_list[0:which_colon]), line_list[which_colon]

def _clean_line(x):
    # Fix some common data quality problems
    x1 = re.sub('^\\*\xa0French:\xa0',    '* French: ', x)
    x1 = re.sub('^\\*\xa0French:',        '* French:', x1)
    x1 = re.sub('^\\*\xa0Finnish:\xa0',   '* Finnish: ', x1)
    x1 = re.sub('^\\*\xa0Finnish:',       '* Finnish:', x1)
    x1 = re.sub('^\\*\xa0Chinese:\xa0',   '* Chinese: ', x1)
    x1 = re.sub('^\\*\xa0Chinese:',       '* Chinese:', x1)
    x1 = re.sub('^\\*:\xa0Mandarin:',     '*: Mandarin:', x1)
    x1 = re.sub('^\\*:\xa0Mandarin:\xa0', '*: Mandarin: ', x1)

    x1 = re.sub('^\\*Spanish:',            '* Spanish:', x1)
    x1 = re.sub('^\\*French:',             '* French:', x1)
    x1 = re.sub('^\\*Chinese:',            '* Chinese:', x1)
    x1 = re.sub('^\\*:Mandarin: ',        '*: Mandarin: ', x1)

    x1 = re.sub('^\\*\\* Chungli Ao:', '*: Chungli Ao:', x1)
    return x1

def _process_mainspace_page(opf, otf_writer, title, word, ctr):
    lines = word.wikitext.split('\n')
    english_entries = 0
    in_english = False
    pending_trec = False
    for line in lines:
        if line == '==English==':
            if not english_entries:  # only write once per file
                opf.write(title + '\t' + str(word.revision)
                   + '\t' + word.timestamp + '\n')
            english_entries += 1
            # write at least once for pages with English entry
            pending_trec = True
            trec = TransRec()
            trec.title = title
            trec.eeseq = str(ctr + english_entries)
            in_english = True
            in_trans = False
        elif (line.startswith('==')
                and not line.startswith('===')):
            in_english = False
            in_trans = False
        elif (in_english and line.startswith('===')
                and not line.startswith('====')):
            trec.h3 = line[3:len(line)-3]
            trec.h4 = ''
            trec.h5 = ''
        elif (in_english and line.startswith('====')
                and not line.startswith('=====')):
            trec.h4 = line[4:len(line)-4]
            trec.h5 = ''
        elif (in_english and line.startswith('=====')
                and not line.startswith('======')):
            trec.h5 = line[5:len(line)-5]
        elif in_english:
            if line.startswith('{{trans-top'):
                lev1 = ''
                lev2 = ''
                lev3 = ''
                in_trans = True
                trec.transtop_line = line
                trec.tteseq = str(int(trec.tteseq) + 1)
            if in_trans and line.startswith('{{trans-bottom}}'):
                trec.lev1 = ''
                trec.lev2 = ''
                trec.lev3 = ''
                trec.has_trans = 'N'
                trec.trans = ''
                writerow(otf_writer, trec)
                pending_trec = False
                in_trans = False
            if in_trans and line.startswith('*') and ':' in line:
                # don't clean this page, since none of the headers have
                # spacing, so fixing the few we fix causes wrong assignment
                # of level-2 headers since the others aren't seen
                if title != 'Thucydides':
                    line = _clean_line(line)
                if line.startswith('* '):
                    ok, left, right = split_line(line, which_colon=1)
                    if ok:
                        trec.trans = right
                        trec.has_trans = right and 't-needed' not in right
                        trec.lev1 = left
                        trec.lev2 = ''
                        trec.lev3 = ''
                        writerow(otf_writer, trec)
                        pending_trec = False
                    else:
                        print(f'WARNING: BAD (* )! {trec.title=} {trec.transtop_line=} {line=}')
                elif line.startswith('*: '):
                    ok, left, right = split_line(line, which_colon=2)
                    if ok:
                        trec.trans = right
                        trec.has_trans = right and 't-needed' not in right
                        trec.lev2 = left
                        trec.lev3 = ''
                        writerow(otf_writer, trec)
                        pending_trec = False
                    else:
                        print(f'WARNING: BAD (*: )! {trec.title=} {trec.transtop_line=} {line=}')
                elif line.startswith('*:: '):
                    ok, left, right = split_line(line, which_colon=3)
                    if ok:
                        trec.trans = right
                        trec.has_trans = right and 't-needed' not in right
                        trec.lev3 = left
                        writerow(otf_writer, trec)
                        pending_trec = False
                    else:
                        print(f'WARNING: BAD (*:: )! {trec.title=} {trec.transtop_line=} {line=}')
                elif line.startswith('*::: '):
                    print(f'WARNING: *:::! {trec.title=} {trec.transtop_line=} {trec.lev1=}, {trec.lev2=} {trec.lev3=} {line=}')
                elif line.startswith('*:::: '):
                    print(f'WARNING: *::::! {trec.title=} {trec.transtop_line=} {trec.lev1=}, {trec.lev2=} {trec.lev3=} {line=}')
                elif line.startswith('*'):
                    print(f'WARNING: OTHER_W_COLON (*)! {trec.title=} {trec.transtop_line=} {line=}')
            elif in_trans and line.startswith('*'):
                print(f'WARNING: OTHER_W_COLON (*)! {trec.title=} {trec.transtop_line=} {line=}')
    if pending_trec:
        trec.tteseq = ''
        trec.h3 = ''
        trec.h4 = ''
        trec.h5 = ''
        writerow(otf_writer, trec)
    return english_entries

#-----------------------------------------------------------------------------
# Public Functions
#-----------------------------------------------------------------------------
def extract_enwk_tr_long(input_file, output_trans_file,
                       output_page_file, max_pages=None):
    '''Create long file of translations from English Wiktionary dump/export.

    Translation sections are identified by lines starting with
    '{{trans-top' and the section continues until a line starting with
    '{{trans-bottom}}'.

    The function prints to standard output a message every 10000 pages,
    a warning message if a duplicate entry is found in the translation
    table, and final counts for the number of overall pages,
    main-space pages, and English entries processed.

    Parameters
    ----------
    input_file: str
        Dump or file export from English-language Wiktionary. Note that
        dump files are deprecated by Wikimedia, but there is currently
        (August, 2026) a bug where common pages are dropped from the
        file export. See: https://phabricator.wikimedia.org/T431872.
    max_pages: int or None
        Specify maximum number of pages to process. None will process all
        pages.
    output_trans_file: str
        File name of output translation file. This contains a record for
        each first, second, or third-level language heading in each
        entry in the translation table(s) for the English-language entry
        for all pages.
        Translation table entries are lines starting with
        `{{trans-top`. If no entries are found for a page, a single output
        record is written with `page` populated and all other fields ''.
        The output file contains the following variables:
        - page: Title of the page
        - tteseq: Sequence number for translation table entries on the
                page, starting at 1
        - transtop_line: the line containing the template whose name
                starts with 'transtop'
        - h3:   Third-level header for section with translation table
        - h4:   Fourth-level header for section with translation table
        - h5:   Fifth-level header for section with translation table
        - lang_name_b1: First-level header (including the language name and
                bullet) within one section of a translation table. These
                are from lines formatted as '* [LANGUAGE NAME]:', but the
                ':' is not included in the output. In cases where the
                headings are hiearchical / indented, this value is stored
                and repeated on the file records that give the later
                headings. For example, for Serbo-Croatian, there will be
                one row with `lang_name_b1 == '* Serbo-Croatian'` and
                `trans` empty, and then a row with
                `lang_name_b1 == '* Serbo-Croatian'` and
                `lang_name_b2 == '*: Cyrillic'` with `trans` populated, and
                then a row with
                `lang_name_b1 == '* Serbo-Croatian'` and
                `lang_name_b2 == '*: Latin'` with `trans` populated.

                Lastly, note that this field is simply any text starting
                with '* ' until a colon. We do not check here whether the
                text actually contains a language name.
        - lang_name_b2: Second-level header within one section of a
                translation table. These are from lines formatted as
                '*: [LANGUAGE NAME]:'.
        - lang_name_b3: Third-level header within one section of a
                translation table. These are from lines formatted as
                '*: [LANGUAGE NAME]:'.
        - has_trans: Indicates Y/N if a translation is present. This is
                determined by checking `trans != ''` and
                `'t-needed' not in trans`
        - trans: Translation from the translation table (i.e., text after
                the colon following the language name).
                `str.strip()` is called on the text before saving.
    output_page_file: str
        File name of output file with page information. This file will
        contain the variables `page`, `revision`, `timestamp`.

    Returns
    -------
    None. The function is called for the side effect of creating the
    output files.
    '''
    page_counter = 0
    main_page_counter = 0
    english_entry_counter = 0

    with (bz2.open(input_file, 'rb') as f,
          open(output_page_file, 'w', encoding='utf-8') as opf,
          open(output_trans_file, 'w', encoding='utf-8', newline='') as otf,
         ):
        opf.write('page\trevision\ttimestamp\n')
        writer = csv.writer(otf, delimiter='\t',
                            quoting=csv.QUOTE_NONE,
                            quotechar=None,
                            lineterminator='\n')
        writer.writerow(['page','eeseq','tteseq','transtop_line','h3','h4',
                         'h5','lang_name_b1','lang_name_b2','lang_name_b3',
                         'has_trans','trans'])
        context = ET.iterparse(f, events=('end',))

        _, root = next(context)

        for event, elem in context:
            if event == 'end' and elem.tag == f'{XMLNS}page':
                page_counter = page_counter + 1
                title = elem.find(f'{XMLNS}title').text
                #print(title)

                if page_counter % 10000 == 0:
                    print(f'{page_counter=}')
                if max_pages is not None and page_counter == max_pages:
                    break

                # limit to pages in the main namespace. That is, the pages for
                # words and their definitions. Omits pages like
                # 'Wiktionary:Translations', etc.
                if ':' not in title:
                    main_page_counter = main_page_counter + 1
                    word = PageInfo()
                    _update_word_from_xml_dump(word, elem)
                    if not word.wikitext:
                        print(f'WARNING: empty wikitext {title=}')
                    else:
                        cnt = _process_mainspace_page(opf, writer,
                            title, word, english_entry_counter)
                        english_entry_counter += cnt
                # Clear element once it's processed
                elem.clear()
                # Root will keep references to all of its already-cleared
                # children until it is also cleared
                root.clear()

    print(f'\n{page_counter=}')
    print(f'{main_page_counter=}')
    print(f'{english_entry_counter=}')
    print('\n')
