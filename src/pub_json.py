import re
import os
import pandas as pd
import bibtexparser
import requests
from bs4 import BeautifulSoup
from os import walk



def publication_json(bib_ID):

    parser = bibtexparser.bparser.BibTexParser(common_strings=True)

    bibs = {}
    pub_data = []

    filepath = '../dat/acl_anthology/bib/' + bib_ID + '.bib'
    f = open(filepath)
    bib = bibtexparser.loads(f.read(), parser=parser)
    try:
        bibs.update(
            [(entry['url'].split('/')[-1], entry) for entry in bib.entries
             if ('author' in entry and 'pages' in entry and 'url' in entry)])

        for k, v in bibs.items():
            print('Scanning publication', k)

            pub_dict = {}
            pub_dict['id'] = k
            pub_dict['title'] = v['title']
            del v['title']

            pub_dict['authors'] = v['author'].split('  and\n')

            del v['author']

            pub_dict['emails'] = get_emails(k, pub_dict['authors'])
            pub_dict['emails'] = email_match(pub_dict['authors'], pub_dict['emails'])

            pub_dict['author_id'] = author_id(k)

            del v['ENTRYTYPE']
            del v['ID']
            pub_dict.update(v)

            pub_data.append(pub_dict)


    except:  # some workshops have different bib file format

        bibs.update(
            [(entry['ID'], entry) for entry in bib.entries
             if ('author' in entry and 'pages' in entry and 'url' in entry)])

        for k, v in bibs.items():
            print('Scanning publication', k)

            pub_dict = {}
            pub_dict['id'] = k
            pub_dict['title'] = v['title']
            del v['title']

            pub_dict['authors'] = v['author'].split('  and\n')
            del v['author']

            pub_dict['emails'] = get_emails(k, pub_dict['authors'])
            pub_dict['emails'] = email_match(pub_dict['authors'], pub_dict['emails'])

            pub_dict['author_id'] = author_id(k)

            del v['ENTRYTYPE']
            del v['ID']
            pub_dict.update(v)

            pub_data.append(pub_dict)

    df = pd.DataFrame(pub_data)
    df.to_json('../dat/acl_anthology/json/' + bib_ID + '.json', orient='records')
    print("Added " + bib_ID + ".json to file")




def get_emails(txtfile, authors):
    filepath = os.path.join('/Users/Chloe/PycharmProjects/nlp_ranking/data-collection/txt/', txtfile + '.txt')

    doc = []
    n = 0
    fin = open(filepath)
    for line in fin:
        line = line.strip()
        if line:
            doc.append(line)
            n += len(line)
            if n > 2000: break
    doc = ' '.join(doc)

    re_email = re.compile('[({\[]?\s*([a-z0-9\.\-_]+(?:\s*[,;|]\s*[a-z0-9\.\-_]+)*)\s*[\]})]?\s*@\s*([a-z0-9\.\-_]+\.[a-z]{2,})')

    emails = []
    if re_email.findall(doc) is not None:
        for m in re_email.findall(doc):
            ids = m[0].replace(';', ',').replace('|', ',')
            domain = m[1]

            if ',' in ids:
                emails.extend([ID.strip() + '@' + domain for ID in ids.split(',')])
            else:
                emails.append(ids + '@' + domain)

        fin.close()

    # fixing firstname.lastname email types
    re_name1 = re.compile('firstname.lastname@([a-z]+.[a-z]+(-[a-z]+.[a-z]+)?)')
    re_name2 = re.compile('first-name.last-name@([a-z]+.[a-z]+(-[a-z]+.[a-z]+)?)')
    re_name3 = re.compile('first.last@([a-z]+.[a-z]+(-[a-z]+.[a-z]+)?)')
    re_name4 = re.compile('\{first-name.last-name\}@([a-z]+.[a-z]+(-[a-z]+.[a-z]+)?)')
    re_name5 = re.compile('name.surname@([a-z]+.[a-z]+(-[a-z]+.[a-z]+)?)')
    re_name6 = re.compile('\{firstname.surname\}@([a-z]+.[a-z]+(-[a-z]+.[a-z]+)?)')

    re_name_list = [re_name1, re_name2, re_name3, re_name4, re_name5, re_name6]

    for email in emails:
        if any(regex.findall(email) for regex in re_name_list):
            for m in re_email.findall(email):
                if any(c in m[0] for c in ['first.last', 'name.surname', 'firstname', 'first-name']):
                    domain = m[1]

            for author in authors:
                try:
                    f = author.split(', ')[1].split(' ')[0]
                    l = author.split(', ')[0]
                except:
                    f = author.split(' ')[0]
                    l = author.split(' ')[1]
                if all(f.lower() not in e for e in emails):
                    emails.append(f.lower() + '.' + l.lower() + '@' + domain)

            emails.remove(email) # remove firstname.lastname email template from emails


    return emails






from fuzzywuzzy import fuzz
import numpy as np

def email_match(authors, emails):

    author_list = authors[:] # create a copy of authors (not changing the input)

    # result = reordered emails list
    result = [''] * len(author_list)

    matrix = []
    for email in emails:
        ratios = []
        for author in author_list:

            try:
                email_id = email.split('@')[0]

                try:
                    lname = author.split(', ')[0].lower()
                    fname = author.split(', ')[1].lower()
                except:
                    fname = author.split(' ')[0].lower()
                    lname = author.split(' ')[1].lower()


                # firstname
                fname

                # lastname
                lname

                # f (m) l
                initial = ''.join([i[0].lower() for i in re.findall(r"[\w']+", fname)]) + ''.join(
                    [j[0].lower() for j in re.findall(r"[\w']+", lname)])

                # f (m) lastname
                f_lastname = ''.join([i[0].lower() for i in re.findall(r"[\w']+", fname)]) + lname

                # firstname lastname
                name = fname + lname

                # lastname f (m)
                lastname_f = lname + ''.join([i[0].lower() for i in re.findall(r"[\w']+", fname)])


                ratios.append([fuzz.ratio(lname, email_id), fuzz.ratio(fname, email_id),
                               fuzz.ratio(initial, email_id), fuzz.ratio(f_lastname, email_id),
                               fuzz.ratio(name, email_id), fuzz.ratio(lastname_f, email_id)])


            except:
                ratios.append([0] * 6) # because there're 6 patterns


        ratios = np.array(ratios)
        ratios = np.transpose(ratios)
        matrix.extend(ratios)


    matrix = np.array(matrix)

    indices = {}
    for score in sorted(set(matrix.flat), reverse=True):
            cord = np.where(matrix == score)
            for c in list(zip(cord[0], cord[1])):
                if c[0]//6 not in indices.keys() and c[1] not in indices.values():
                    indices[c[0]//6] = c[1]

                if len(indices) == len(emails):
                    break


    for k,v in indices.items():
        result[v] = emails[k]

    return result



def author_id(pub_id):
    r = requests.get('https://www.aclweb.org/anthology/' + pub_id)
    soup = BeautifulSoup(r.text, 'html.parser')

    author_ids = [a.get('href').split('/')[-2] for a in soup.find('p', class_='lead').find_all('a') if '/people/' in a.get('href')]


    return author_ids








if __name__ == '__main__':


    all_bib = [filename[:-4] for (dirpath, dirnames, filenames) in walk('../dat/acl_anthology/bib/') for filename in filenames if '.bib' in filename]

    for bib_id in all_bib:
        publication_json(bib_id)

