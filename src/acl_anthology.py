import requests
from bs4 import BeautifulSoup
import pandas as pd
import bibtexparser
import os
import os.path
from os import walk

def get_bib(venues):

    url = 'https://www.aclweb.org/anthology/'

    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    tables = soup.find('div', class_ = 'col-12 col-xl-10 col-xl-width-auto').find_all('table')

    years = [10 + x for x in range(10)] # 10-19

    # bib_map = pd.DataFrame(columns=['venue', 'ID', 'title'])
    bib_map = pd.read_csv('bib_map.csv')


    for table in tables:
        for tr in table.find('tbody').find_all('tr'):
            venue = tr.find('th').text
            if venue in venues:
                for td in tr.find_all('td'):
                    try:
                        if int(td.text) in years:
                            cite = 'https://www.aclweb.org' + td.find('a').get('href')
                            print('Getting bib files for venue ' + venue + ' in year 20' + td.text)
                            for k,v in get_bibFiles(cite).items():
                                bib_map = bib_map.append({'venue': venue, 'ID': k, 'title': v}, ignore_index=True)
                    except:
                        continue

    bib_map.to_csv('bib_map.csv', index=False)

def get_bibFiles(url):

    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    div = soup.find('section').find_all('div')

    result = {}

    for d in div:
        if d.get('id') is not None and 'abstract' not in d.get('id'):
            id = d.get('id').upper()
            title = d.find('h4').select("a[class='align-middle']")[0].text
            bib = d.find('h4').find('span').find('a', class_ = 'badge badge-secondary align-middle mr-1').get('href')

            bibfile = requests.get('https://www.aclweb.org' + bib)
            filename = bib.split('/')[-1]
            filepath = './bib/' + filename
            with open(filepath, 'wb') as f:
                print('Writing file ' + filename + '...')
                f.write(bibfile.content)

            result[id] = title

    return result

def filter_bib():
    bibmap = pd.read_csv('bib_map.csv')

    i_bib = pd.read_csv('bib_map.tsv', sep='\t', names=['ID', 'Score', 'Type'])

    for (dirpath, dirnames, filenames) in walk('./bib/'):
        include_ws = [filename[:-4] for filename in filenames if 'W' in filename]

    include = []
    for id in bibmap['ID']:
        if id in list(i_bib['ID']) or 'J' in id:
            include.append(1)
        else:
            include.append(0)

    bibmap['include'] = include

    # student research workshop, demonstration

    interested = ['P19-1', 'P18-1', 'P18-2', 'K18-1', 'D18-1', 'N19-1', 'N19-2', 'N18-1', 'N18-2', 'N18-3', 'S19-1',
                'S19-2', 'S18-1', 'S18-2', 'C18-1', 'D19-1', 'D19-3', 'K19-1']

    for i, b in bibmap.iterrows():
        if 'student research workshop' in b['title'].lower() or 'demonstration' in b['title'].lower() \
                or b['venue'] == 'TACL' or b['ID'] in interested:
            if b['include'] == 0:
                bibmap.iloc[i,3] = 1
        if b['venue'] == 'WS' and b['ID'] in include_ws:
            bibmap.iloc[i,3] = 1
        if 'tutorial' in b['title'].lower():
            bibmap.iloc[i,3] = 0

    bibmap = bibmap[bibmap['include'] == 1]
    bibmap = bibmap.drop(columns='include')

    type = ['']*bibmap.shape[0]
    bibmap['type'] = type


    # type = journal, conference, workshop, demonstration

    journal = ['CL', 'TACL']
    con = ['ACL', 'NAACL', 'EMNLP', 'CoNLL', 'EACL', 'COLING', 'IJCNLP']


    for i, b in bibmap.iterrows():

        if any(j == b['venue'] for j in journal):
            b['type'] = 'journal'
        elif any(c == b['venue'] for c in con):
            b['type'] = 'conference'
        elif b['venue'] == '*SEMEVAL':
            b['type'] = 'workshop'
        else:
            b['type'] = 'workshop'

        if 'workshop' in b['title'].lower():
            b['type'] = 'workshop'
        elif 'demonstration' in b['title'].lower():
            b['type'] = 'demonstration'

    bibmap['year'] = bibmap.ID.apply(lambda x: '20' + x[1:3])

    bibmap = bibmap.rename(columns={'title': 'description', 'ID': 'id'})

    bibmap.to_json('bibmap.json', orient='records')



def downloadPDF():

    bibmap = pd.read_json('bibmap.json')
    dir = './bib/'
    parser = bibtexparser.bparser.BibTexParser(common_strings=True)

    files = []
    for (dirpath, dirnames, filenames) in walk('./txt/'):
        for filename in filenames:
            if '.txt' in filename:
                files.append(filename.split('.')[0])


    for ID in bibmap['id'].tolist():

        bibs = {}
        filepath = os.path.join(dir, ID + '.bib')
        f = open(filepath)
        bib = bibtexparser.loads(f.read(), parser=parser)

        bibs.update(
            [(entry['url'].split('/')[-1], entry) for entry in bib.entries
             if ('author' in entry and 'pages' in entry and 'url' in entry)])

        bib.entries = []
        print('Viewing files in ' + ID)

        for k, v in bibs.items():
            if k not in files:
                pdf = requests.get(v['url'] + '.pdf')
                filepath = './pdf/' + k + '.pdf'
                with open(filepath, 'wb') as pdf_file:
                    print('Saving PDF file ' + k)
                    pdf_file.write(pdf.content)

                    files.append(k)


from tika import parser


def pdf2txt():
    files = []
    for (dirpath, dirnames, filenames1) in walk('./txt/'):
        for filename1 in filenames1:
            if '.txt' in filename1:
                files.append(filename1.split('.')[0])



    for (dirpath, dirnames, filenames) in walk('./pdf/'):
        for filename in filenames:
            if '.pdf' in filename:
                filename = filename.split('.')[0]
                # if filename not in files:
                print(filename)
                raw = parser.from_file('./pdf/' + filename + '.pdf')

                filepath = './txt/' + filename + '.txt'
                txt_file = open(filepath, 'w')
                print('Converting ' + filename + ' to txt file')
                try:
                    txt_file.write(raw['content'])
                    txt_file.close()
                    files.append(filename)
                except:
                    continue




if __name__ == '__main__':
    # venues = ['ACL', 'CL', 'CoNLL', 'EACL', 'EMNLP', 'NAACL', '*SEMEVAL', 'TACL', 'WS', 'COLING', 'IJCNLP']
    # get_bib(venues)
    filter_bib()
    # downloadPDF()
    # pdf2txt()
