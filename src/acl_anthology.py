import requests
from bs4 import BeautifulSoup
import pandas as pd
import bibtexparser
import os
import os.path
from os import walk


def crawl_aclbib(bib_map_txt):
    map = pd.read_csv(bib_map_txt, sep='\t', header=None)

    bibmap = pd.DataFrame(columns=['venue', 'id', 'year', 'type', 'description'])

    for event,issues in map.values.tolist():

        url = 'https://www.aclweb.org/anthology/events/' + event
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')

        div = soup.find('section').find_all('div')

        for d in div:
            if d.get('id') is not None and 'abstract' not in d.get('id'):
                id = d.get('id').upper()
                description = d.find('h4').select("a[class='align-middle']")[0].text

                if id not in issues.split(',') and issues != 'all':
                    continue

                bib = d.find('h4').find('span').find('a', class_='badge badge-secondary align-middle mr-1').get('href')

                bibfile = requests.get('https://www.aclweb.org' + bib)
                filename = bib.split('/')[-1]
                filepath = '../dat/acl_anthology/' + filename
                with open(filepath, 'wb') as f:
                    print('Writing file ' + filename + '...')
                    f.write(bibfile.content)


                venue = event.split('-')[0].upper()
                if venue == 'CONLL': venue = 'CoNLL'

                year = event.split('-')[1]

                journal = ['CL', 'TACL']
                con = ['ACL', 'NAACL', 'EMNLP', 'CoNLL', 'EACL', 'COLING', 'IJCNLP']
                ws = ['SEMEVAL']


                if 'workshop' in description.lower():
                    type = 'workshop'
                elif 'demonstration' in description.lower():
                    type = 'demonstration'
                elif venue in journal:
                    type = 'journal'
                elif venue in con:
                    type = 'conference'
                elif venue in ws:
                    type = 'workshop'
                else:
                    type = 'workshop'

                if id not in bibmap['id'].tolist(): # WS may contain issues of other venues (e.g. CoNLL 2014)

                    bibmap = bibmap.append({'venue': venue, 'id': id, 'year': year, 'type': type, 'description': description}, ignore_index=True)



    bibmap.to_json('../dat/bibmap.json', orient='records')



def downloadPDF(dir, bibfile_ID):

    parser = bibtexparser.bparser.BibTexParser(common_strings=True)

    bibs = {}
    filepath = os.path.join(dir, bibfile_ID + '.bib')
    f = open(filepath)
    bib = bibtexparser.loads(f.read(), parser=parser)

    bibs.update(
        [(entry['url'].split('/')[-1], entry) for entry in bib.entries
         if ('author' in entry and 'pages' in entry and 'url' in entry)])

    bib.entries = []
    print('Viewing files in ' + bibfile_ID)

    for k, v in bibs.items():
        pdf = requests.get(v['url'] + '.pdf')
        filepath = '../data-collection/pdf/' + k + '.pdf'
        with open(filepath, 'wb') as pdf_file:
            print('Saving PDF file ' + k)
            pdf_file.write(pdf.content)



from tika import parser

# converting everything in /pdf/ folder to txt
def pdf2txt():


    for (dirpath, dirnames, filenames) in walk('../data-collection/pdf/'):
        for filename in filenames:
            if '.pdf' in filename:
                filename = filename.split('.')[0]
                print(filename)
                raw = parser.from_file('../data-collection/pdf/' + filename + '.pdf')

                filepath = '../data-collection/txt/' + filename + '.txt'
                txt_file = open(filepath, 'w')
                print('Converting ' + filename + ' to txt file')
                try:
                    txt_file.write(raw['content'])
                    txt_file.close()
                except:
                    continue




if __name__ == '__main__':

    bib_map_txt = '../dat/bib_map.txt'
    # crawl_aclbib(bib_map_txt)

    dir = '../dat/acl_anthology/'
    # bib files of additional issues
    add_bib = ['W19-86', 'W19-85', 'D19-66', 'W19-63', 'D19-50', 'D19-55', 'D19-56', 'W19-78', 'W19-77', 'D19-60', 'D19-52', 'W19-61', 'W19-90', 'W19-75', 'D19-54', 'W19-84', 'W19-59', 'D19-62', 'W19-64', 'W19-79', 'W19-87', 'D19-65', 'D19-61', 'W19-31', 'D19-59', 'W19-83', 'W19-80', 'W19-81', 'W19-65', 'D19-58', 'W19-76', 'D19-57', 'D19-63', 'D19-64', 'D19-53', 'W19-89', 'W19-62', 'D19-51']

    #
    # for bid_id in add_bib:
    #     downloadPDF(dir, bid_id)
    # pdf2txt()
