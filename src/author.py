import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import json
from os import walk




def author_pub(issue_id):

    author = pd.read_json('../dat/author.json')
    author.columns = ['author_id', 'firstname', 'lastname', 'publications']
    author = author.replace(np.nan, '', regex=True)
    author_pub = author.set_index(author.author_id).T.to_dict()


    pub_json = json.load(open('../dat/acl_anthology/json/' + issue_id + '.json'))

    print('Adding pubs from ' + issue_id)

    i = 0
    for pub in pub_json:

        pub_id = pub['id']

        for author_id in pub['author_id']:

            if author_id not in author_pub.keys():
                author_webpage = 'https://www.aclweb.org/anthology/people/' + author_id[0] + '/' + author_id
                r_author = requests.get(author_webpage)
                a_soup = BeautifulSoup(r_author.text, 'html.parser')
                firstname = a_soup.find('span', class_='font-weight-normal').text
                lastname = a_soup.find('span', class_='font-weight-bold').text

                author_pub[author_id] = {'author_id': author_id, 'firstname': firstname, 'lastname': lastname, 'publications': [pub_id]}

            else:
                if pub_id not in author_pub[author_id]['publications']:
                    author_pub[author_id]['publications'].append(pub_id)

        i += 1
        print(str(len(pub_json) - i) + ' more publications to add')



    with open('../dat/author.json', 'w') as json_file:
        json.dump(list(author_pub.values()), json_file)


    print('Added ' + issue_id + ' to author.json')











if __name__ == '__main__':

    all_pub = [filename[:-5] for (dirpath, dirnames, filenames) in walk('../dat/acl_anthology/json/') for filename in filenames if '.json' in filename][160:]

    for issue_id in all_pub:
        author_pub(issue_id)






