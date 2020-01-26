import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from os import walk



def add_new_pub(new_pub):
    dat = pd.read_csv('author_pub.txt', sep='\t', header=None)
    dat.columns = ['author_id', 'firstname', 'lastname', 'publications']
    dat = dat.replace(np.nan, '', regex=True)
    author_pub = dat.set_index(dat.author_id).T.to_dict()


    i = 0
    for pub_id in new_pub:
        r = requests.get('https://www.aclweb.org/anthology/' + pub_id)
        soup = BeautifulSoup(r.text, 'html.parser')


        author_ids = [a.get('href').split('/')[-2] for a in soup.find('p', class_ = 'lead').find_all('a') if '/people/' in a.get('href')]

        for id in author_ids:
            if id not in author_pub.keys():
                author_webpage = 'https://www.aclweb.org/anthology/people/' + id[0] + '/' + id
                r_author = requests.get(author_webpage)
                a_soup = BeautifulSoup(r_author.text, 'html.parser')
                firstname = a_soup.find('span', class_='font-weight-normal').text
                lastname = a_soup.find('span', class_='font-weight-bold').text

                author_pub[id] = {'author_id': id, 'firstname': firstname, 'lastname': lastname, 'publications': pub_id}

            else:
                if pub_id not in author_pub[id]['publications']:
                    author_pub[id]['publications'] += ',' + pub_id




        i += 1
        print(str(len(new_pub)-i) + ' more publications to add')


        with open('author_pub.txt', 'w') as f:
            for v1 in author_pub.values():
                f.write('\t'.join([v2 for v2 in v1.values()]) + '\n')



def author2json():

    dat = pd.read_csv('author_pub.txt', sep='\t', header=None)
    dat.columns = ['author_id', 'firstname', 'lastname', 'publications']

    dat['publications'] = dat['publications'].str.split(',')

    dat.to_json('author.json', orient='records')




if __name__ == '__main__':
    # new_pub = [file[:-4] for (dirpath, dirnames, filenames) in walk('./pdf/') for file in filenames]
    #
    # add_new_pub(new_pub)
    author2json()






