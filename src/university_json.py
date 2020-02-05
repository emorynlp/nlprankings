import pandas as pd
from os import walk
from collections import Counter
from collections import defaultdict


# create json file with universities and its corresponding publications
# will count as an university if the email domain contains .edu
def university_pub():

    uni = {}

    for (dirpath, dirnames, filenames) in walk('../dat/acl_anthology/'):
        for filename in filenames:
            if '.json' in filename:
                pub = pd.read_json(dirpath + filename)
                records = pub.to_dict(orient='records')

                for record in records:
                    domains = [parse_email(e.split('@')[-1]) for e in record['emails']]
                    c = Counter(domains)
                    for key in c.keys():
                        if 'edu' in key.split('.'):
                            if key in uni.keys():
                                # (pub_id, contribution_percentage)
                                uni[key].append((record['id'], c[key]/len(record['authors'])))
                            else:
                                uni[key] = [(record['id'], c[key]/len(record['authors']))]



    university_list = []
    for k,v in uni.items():
        university_list.append({'domain_id': k, 'publications': v})

    df = pd.DataFrame(university_list)
    df.to_json('../dat/university.json', orient='records')






def parse_email(domain):
    if '.edu' in domain:
        d = domain.split('.')
        return '.'.join(d[d.index('edu')-1:])
    else:
        return domain





if __name__ == '__main__':
    university_pub()


