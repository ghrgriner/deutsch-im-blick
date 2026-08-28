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
    ('transtop_line', str, field(default='')),
    ('h3',  str, field(default='')),
    ('h4',  str, field(default='')),
    ('trans_count', int, field(default=0)),
                                      ])
#-----------------------------------------------------------------------------
# Private Functions
#-----------------------------------------------------------------------------
def _update_word_from_xml_dump(word, elem):
    revision_elem = elem.find(f'{XMLNS}revision')
    word.revision = int(revision_elem.find(f'{XMLNS}id').text)
    word.timestamp = revision_elem.find(f'{XMLNS}timestamp').text
    word.wikitext = revision_elem.find(f'{XMLNS}text').text

def _check_for_duplicate_lang_codes(languages):
    counts = Counter(languages)
    dup_lang_codes = [item for item, count in counts.items() if count > 1]
    if dup_lang_codes:
        print(dup_lang_codes)
        raise ValueError('Duplicate language codes in all_languages.py')

def writerow(otf_writer, trec):
    data = ([trec.title, trec.h3, trec.h4, trec.transtop_line]
            + [ str(item) for item in trec.transd.values() ]
            + [str(trec.trans_count)])
    for item in data:
        if '\t' in item or '\r' in item or '\n' in item:
            print(f'BAD CHAR in {trec.title=}, {item=}')
    clean_data = [ item.replace('\t',' ').replace('\r',' ').replace('\n',' ')
                   for item in data ]
    otf_writer.writerow(clean_data)

def _process_mainspace_page(opf, otf_writer, title, word, languages):
    lines = word.wikitext.split('\n')
    english_entries = 0
    pending_trec = False
    in_english = False
    for line in lines:
        if line == '==English==':
            if not english_entries:  # only write once per file
                opf.write(title + '\t' + str(word.revision)
                   + '\t' + word.timestamp + '\n')
            english_entries += 1
            if pending_trec:
                writerow(otf_writer, trec)
            trec = TransRec()
            trec.title = title
            pending_trec = True
            trec.transd = { item[0]: '' for item in languages }
            in_english = True
            in_trans = False
        elif (line.startswith('==')
                and not line.startswith('===')):
            # saves about 10 seconds of 9 min run time
            # but drops translations for 'nine' in July 2026 feed
            #if line != '==Translingual==':
            #    if pending_trec:
            #        writerow(otf_writer, trec)
            #    return english_entries
            in_english = False
            in_trans = False
        elif (in_english and line.startswith('===')
                and not line.startswith('====')):
            h3 = line[3:len(line)-3]
            h4 = ''
        elif (in_english and line.startswith('====')
                and not line.startswith('=====')):
            h4 = line[4:len(line)-4]
        elif in_english:
            if line.startswith('{{trans-top'):
                in_trans = True
                if pending_trec and trec.transtop_line == '':
                    trec.transtop_line = line
                    trec.h3 = h3
                    trec.h4 = h4
                else:
                    writerow(otf_writer, trec)
                    trec.transtop_line = line
                    trec.h3 = h3
                    trec.h4 = h4
                    trec.trans_count = 0
                    trec.transd = { item[0]: '' for item in languages }
            if line.startswith('{{trans-bottom}}'):
                in_trans = False
            if ((in_trans and line.startswith('* ')
              and ':' in line
              and line.split(':')[1].strip()
              and 't-needed' not in line)):
                trec.trans_count = trec.trans_count + 1
            for lang, langtxt in languages:
                startpos = len(langtxt)
                if in_trans and line.startswith(langtxt):
                    if trec.transd[lang]:
                        print(f'WARNING: {lang} already populated! {title=}, '
                            f'{trec.transtop_line=} old={trec.transd[lang]} '
                            f'new={line[startpos:].strip()}')
                    trec.transd[lang] = line[startpos:].strip()
                    break
    if pending_trec:
        writerow(otf_writer, trec)
    return english_entries

#-----------------------------------------------------------------------------
# Public Functions
#-----------------------------------------------------------------------------
def extract_enwk_trans(input_file, languages, output_trans_file,
                       output_page_file, max_pages=None):
    '''Create file of translations from English Wiktionary dump/export.

    Translation sections are identified by lines starting with
    '{{trans-top' and the section continues until a line starting with
    '{{trans-bottom}}'.

    The function prints to standard output a message every 10000 pages,
    a warning message if a duplicate entry is found in the translation
    table, and final counts for the number of overall pages,
    main-space pages, and English entries processed.

    Note that the warning message about duplicate entries prints the
    language code (e.g., 'de'), but it's actually the longer text string
    (e.g., '* German:') and not the code used to identify duplicates.

    Parameters
    ----------
    input_file: str
        Dump or file export from English-language Wiktionary. Note that
        dump files are deprecated by Wikimedia, but there is currently
        (August, 2026) a bug where common pages are dropped from the
        file export. See: https://phabricator.wikimedia.org/T431872.
    languages: list[(str, str)]
        List of languages to extract from every translation table.
        Each item in the list is a tuple, where the first element is
        the language code. (This can currently be an arbitrary string,
        but we strongly recommend using the Wiktionary language code
        in case we use this element for more than variable naming in the
        future.) The second element is a string that identifies the
        language in the translation table. The line in the translation
        table that contains the translation should start with this string.
        An exception is raised if the first element is duplicated in
        the list items.

        Note that not all languages can be extracted using this program
        if the text string that starts the line is used for multiple
        languages, which can occur by the line is a subheading. See
        `all_languages.py` for slightly more details.
    max_pages: int or None
        Specify maximum number of pages to process. None will process all
        pages.
    output_trans_file: str
        File name of output translation file. This file will contain the
        variables `page`, `transtop_line`, `trans_count` and translations
        for the requested languages with names `tr_enwk_[LANGCODE]`.
        Note that here `trans_count` counts the number of non-indented
        languages for which the entry is not blank or `t-needed`.
        In particular, it is not only limited to languages in `languages`.
        Note that the extracted translations are not plain text. They
        will still be wrapped in Wiktionary translation templates.
    output_page_file: str
        File name of output file with page information. This file will
        contain the variables `page`, `revision`, `timestamp`.

    Returns
    -------
    None. The function is called for the side effect of creating the
    output files.
    '''
    _check_for_duplicate_lang_codes(languages)

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
        writer.writerow(['page','h3','h4','transtop_line']
            + [ 'tr_enwk_' + item[0] for item in languages ]
            + ['trans_count'])
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
                            title, word, languages)
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
