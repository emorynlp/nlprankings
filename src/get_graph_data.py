import pandas as pd
from os import walk


# author_id, edu_domain, university_name, pub_id, venue, v_id, num_author, year, type
def get_df():
    university_info = pd.read_json('../dat/university_domain_us.json', orient='records')
    bibmap = pd.read_json('../dat/bibmap.json', orient='records')
    bibmap_dict = bibmap.set_index('id').to_dict('index')


    # country-specific university domains
    c_domains = [domain for u_domains in university_info['domain'].tolist() for domain in u_domains]

    domain_ids = {}
    for domains in university_info['domain']:
        for domain in domains:
            domain_ids[domain] = domains[0]

    result = {}

    for (dirpath, dirnames, filenames) in walk('../dat/acl_anthology/json/'):
        for filename in filenames:
            if '.json' in filename:
                pub = pd.read_json(dirpath + filename)
                records = pub.to_dict(orient='records')

                for record in records:
                    author_id = record['author_id']
                    numAuthor = len(author_id)
                    domains = [parse_email(e.split('@')[-1]) for e in record['emails']]
                    pub_id = record['id']
                    venue_id = find_venue(pub_id)
                    venue = bibmap_dict[venue_id]['venue']
                    year = bibmap_dict[venue_id]['year']
                    type = bibmap_dict[venue_id]['type']

                    if type not in ['workshop', 'demonstration']:
                        for i in range(len(domains)):
                            if domains[i] in c_domains:
                                domain = domain_ids[domains[i]]
                                if author_id[i] in result.keys():
                                    result[author_id[i]].append([domain, pub_id, venue_id, numAuthor, venue, year, type])
                                else:
                                    result[author_id[i]] = [[domain, pub_id, venue_id, numAuthor, venue, year, type]]
                    else:
                        try:
                            pages = record['pages'].split('--')
                            num_pages = int(pages[1]) - int(pages[0]) + 1
                        except:  # pages with roman numbers or single page
                            continue

                        if num_pages > 4:

                            for i in range(len(domains)):
                                if domains[i] in c_domains:
                                    domain = domain_ids[domains[i]]
                                    if author_id[i] in result.keys():
                                        result[author_id[i]].append([domain, pub_id, venue_id, numAuthor, venue, year, type])
                                    else:
                                        result[author_id[i]] = [[domain, pub_id, venue_id, numAuthor, venue, year, type]]



    df = pd.DataFrame(result.items(), columns=['authorID', 'v'])

    df = df.explode('v')
    df[['domain', 'pubID', 'venueID', 'numAuthor', 'venue', 'year', 'type']] = pd.DataFrame(df.v.values.tolist(), index=df.index)
    df = df.drop(columns=['v'])

    uni_name = dict(zip(university_info.domain.apply(lambda x: x[0]), university_info.name))
    df['university'] = df['domain'].map(uni_name)


    # print(df.columns)

    df.to_csv('../dat/graph_data.csv')

    return df

def parse_email(domain):
    if '.edu' in domain:
        d = domain.split('.')
        return '.'.join(d[d.index('edu')-1:])
    else:
        return domain


def find_venue(pub_id):
    if 'W' in pub_id or 'D19-5' in pub_id or 'D19-6' in pub_id:
        return pub_id[:-2]
    else:
        return pub_id[:-3]


if __name__ == '__main__':

    get_df()