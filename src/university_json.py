import pandas as pd
from os import walk
from collections import Counter


def university_pub(university_domain_json, country):

    university_info = pd.read_json(university_domain_json, orient='records')

    # country-specific university domains
    c_domains = [domain for u_domains in university_info['domain'].tolist() for domain in u_domains]


    uni = {}

    for (dirpath, dirnames, filenames) in walk('../dat/acl_anthology/json/'):
        for filename in filenames:
            if '.json' in filename:
                pub = pd.read_json(dirpath + filename)
                records = pub.to_dict(orient='records')

                for record in records:
                    domains = [parse_email(e.split('@')[-1]) for e in record['emails']]
                    c = Counter(domains)
                    for key in c.keys():
                        if key in c_domains:
                            if key in uni.keys():
                                # (pub_id, contribution_percentage)
                                uni[key].append((record['id'], c[key]/len(record['authors'])))
                            else:
                                uni[key] = [(record['id'], c[key]/len(record['authors']))]



    university_list = []
    for k,v in uni.items():
        university_list.append({'domain_id': k, 'publications': v})

    df = pd.DataFrame(university_list)

    output_filename = '../dat/university_' + country + '.json'
    df.to_json(output_filename, orient='records')




def parse_email(domain):
    if '.edu' in domain:
        d = domain.split('.')
        return '.'.join(d[d.index('edu')-1:])
    else:
        return domain





if __name__ == '__main__':

    us_uni_info = '../dat/university_domain_us.json'
    country = 'us'
    university_pub(us_uni_info, country)


