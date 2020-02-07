from flask import Flask, request, render_template, redirect
import json
from collections import defaultdict
import pandas as pd
import boto3
from dynamodb_json import json_util
from datetime import datetime
from decimal import Decimal


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
        table = dynamodb.Table('nlp-ranking-logs')

        # journal
        CL = float(request.form['CL'])
        TACL = float(request.form['TACL'])

        # conference
        ACL_C = float(request.form['ACL-C'])
        NAACL_C = float(request.form['NAACL-C'])
        EMNLP_C = float(request.form['EMNLP-C'])
        CoNLL_C = float(request.form['CoNLL-C'])
        EACL_C = float(request.form['EACL-C'])
        COLING = float(request.form['COLING'])
        IJCNLP = float(request.form['IJCNLP'])

        # workshop or demo
        WKSPDEMO = float(request.form['WKSPDEMO'])


        startYear = int(request.form['start-year'])
        endYear = int(request.form['end-year'])

        num_uni = int(request.form['num_uni'])
        num_author = int(request.form['num_author'])

        table.put_item(
            Item={
                'UTCtime': str(datetime.utcnow()),
                'startYear': startYear,
                'endYear': endYear,
                'num_uni': num_uni,
                'num_author': num_author,
                'CL': Decimal(CL),
                'TACL': Decimal(TACL),
                'ACL_C': Decimal(ACL_C),
                'NAACL_C': Decimal(NAACL_C),
                'EMNLP_C': Decimal(EMNLP_C),
                'CoNLL_C': Decimal(CoNLL_C),
                'EACL_C': Decimal(EACL_C),
                'COLING': Decimal(COLING),
                'IJCNLP': Decimal(IJCNLP),
                'WKSPDEMO': Decimal(WKSPDEMO),
            }
        )



        authors,maxYear = get_author_dict(
            CL, TACL, ACL_C, NAACL_C, EMNLP_C, CoNLL_C, EACL_C, COLING, IJCNLP, WKSPDEMO
        )

        rank1,rank2,uni_authors = ranking(authors, startYear, endYear, num_author)
        rank1 = rank1.head(n=num_uni)
        rank1.index = rank1.index + 1

        weights = [CL, TACL, ACL_C, NAACL_C, EMNLP_C, CoNLL_C, EACL_C, COLING, IJCNLP, WKSPDEMO]

        years = list(range(2010, maxYear+1))

        return render_template('home.html', ranking1=rank1, ranking2=rank2, year=[startYear, endYear],
        years=years, weights=list(map(int, weights)), num=[num_uni, num_author], uni_authors=uni_authors)

    else:

        authors,maxYear = get_author_dict(3,3,3,3,3,2,2,2,2,1)

        rank1,rank2,uni_authors = ranking(authors, 2010, maxYear, 100)
        rank1 = rank1.head(n=100)
        rank1.index = rank1.index + 1

        years = list(range(2010, maxYear+1))

        return render_template('home.html', ranking1=rank1, ranking2=rank2, year=[2010, maxYear], years=years,
                               weights=[3,3,3,3,3,2,2,2,2,1], num=[100, 100], uni_authors=uni_authors)


@app.route('/methodology/')
def methodology():
    return render_template("methodology.html");



def get_author_dict(CL,TACL,ACL_C,NAACL_C,EMNLP_C,CoNLL_C,EACL_C,COLING,IJCNLP,WKSPDEMO):

    university = pd.read_json('../dat/university_us.json', orient='records')
    bibmap = json.load(open('../dat/bibmap.json'))

    venue_pub = {}  # only look at publications with authors from an university institution
    for pub_id in [y[0] for x in university['publications'].values.tolist() if x for y in x]:
        venue = find_venue(pub_id)
        if venue in venue_pub.keys():
            venue_pub[venue].append(pub_id)
        else:
            venue_pub[venue] = [pub_id]

    university_info = pd.read_json('../dat/university_info_us.json', orient='records')

    # list of us university domains
    us_domains = [domain for u_domains in university_info['domain'].tolist() for domain in u_domains]


    # scoring each venue type
    score = {'journal': 3, 'conference': 3, 'workshop': 1, 'demonstration': 1}



    # authors = {author_id: {university1_domain: {2019: [score, num_pub], 2018: [score, num_pub]}}}
    authors = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0,0])))
    maxYear = 2010 # take the latest year in the data (initialize at 2010, which is the earliest year)

    for k, v in venue_pub.items():
        bib = next((y for y in bibmap if y['id'] == k), None)
        with open('../dat/acl_anthology/json/' + k + '.json') as p:
            json_file = json.load(p)

            # customized scoring weights
            if bib['venue'] == 'CL':
                venue_score = CL
            elif bib['venue'] == 'TACL':
                venue_score = TACL
            elif bib['venue'] == 'ACL' and bib['type'] == 'conference':
                venue_score = ACL_C
            elif bib['venue'] == 'NAACL' and bib['type'] == 'conference':
                venue_score = NAACL_C
            elif bib['venue'] == 'EMNLP' and bib['type'] == 'conference':
                venue_score = EMNLP_C
            elif bib['venue'] == 'CoNLL' and bib['type'] == 'conference':
                venue_score = CoNLL_C
            elif bib['venue'] == 'EACL' and bib['type'] == 'conference':
                venue_score = EACL_C
            elif bib['venue'] == 'COLING':
                venue_score = COLING
            elif bib['venue'] == 'IJCNLP':
                venue_score = IJCNLP
            elif bib['type'] in ['workshop', 'demonstration']:
                venue_score = WKSPDEMO
            else:
                venue_score = score[bib['type']]

            for pub in [x for x in json_file if x['id'] in v]:
                for i in range(len(pub['authors'])):
                    if pub['emails'][i] != "":
                        uni_domain = parse_email(pub['emails'][i].split('@')[1])
                        if uni_domain in us_domains:
                            author_id = pub['author_id'][i]
                            year = pub['year']
                            if int(year) > maxYear:
                                maxYear = int(year)



                            if bib['type'] not in ['workshop', 'demonstration']:
                                # score
                                authors[author_id][uni_domain][year][0] += 1 / len(pub['authors']) * venue_score
                                # num of publications
                                authors[author_id][uni_domain][year][1] += 1
                            else:
                                try:
                                    pages = pub['pages'].split('--')
                                    num_pages = int(pages[1]) - int(pages[0]) + 1
                                except:  # pages with roman numbers or single page
                                    continue

                                if num_pages > 4:
                                    # score
                                    authors[author_id][uni_domain][year][0] += 1 / len(pub['authors']) * venue_score
                                    # num of publications
                                    authors[author_id][uni_domain][year][1] += 1

    return authors,maxYear





def ranking(authors, startYear, endYear, top_k):

    us_universities = pd.read_json('../dat/university_info_us.json', orient='records')


    # create dictionary with all the possible domains as key, and the domain_id (the first domain) as value
    # such that for university with multiple domains, domains will be "converted" to domain_id for matching purpose
    domain_ids = {}
    for domains in us_universities['domain']:
        for domain in domains:
            domain_ids[domain] = domains[0]



    uni_score = {} # university score rank
    author_score = {}  # author score rank
    # uni_authors = {uni: {author1: [score, num_pub, last_year_pub, href], author2: [score, num_pub, last_year_pub, href]}}
    uni_authors = defaultdict(lambda: defaultdict(lambda: [0, 0, 0, 0]))  # authors in each university, score + num_pub
    for author, institutions in authors.items():
        for institution, years in institutions.items():
            institution = domain_ids[institution] # convert other domains to domain_id
            for year,value in years.items():
                if int(year) in range(startYear, endYear+1):

                    if institution in uni_score.keys():
                        uni_score[institution] += value[0]
                    else:
                        uni_score[institution] = value[0]

                    if author in author_score.keys():
                        author_score[author] += value[0]
                    else:
                        author_score[author] = value[0]

                    uni_authors[institution][author][0] += value[0] # score
                    uni_authors[institution][author][1] += value[1] # num_pub
                    uni_authors[institution][author][2] = int(max(years.keys())) # latest publication year


    # author rank
    author_info = pd.read_json('../dat/author.json', orient='records')
    author_info['firstname'] = author_info.firstname.fillna('')
    author_info['name'] = author_info['firstname'] + ' ' + author_info['lastname']
    author_names = dict(zip(author_info.author_id, author_info.name))

    author_rank = pd.DataFrame(sorted(list(author_score.items()), key=lambda x: x[1], reverse=True)[:top_k],
                               columns=['author_id', 'Score'])
    author_rank['url'] = author_rank['author_id'].str[0] + '/' + author_rank['author_id']
    author_rank['Author'] = author_rank['author_id'].map(author_names)
    author_rank = author_rank.round(2)


    # uni rank
    us_universities['domain_id'] = us_universities['domain'].apply(lambda x: x[0]) # take first domain as key
    us_name = dict(zip(us_universities.domain_id, us_universities.name))

    rank = pd.DataFrame(sorted(list(uni_score.items()), key=lambda x: x[1], reverse=True), columns=['domain', 'Score'])
    rank = rank[rank['domain'].isin(us_name.keys())]

    rank['Institution'] = rank['domain'].map(us_name)
    rank = rank.round(2)
    rank = rank.reset_index(drop=True)

    # rounding & sorting by individual author scores
    for u,authors in uni_authors.items():
        for author,v in authors.items():
            v[0] = round(v[0], 2)
            v[3] = author[0] + '/' + author   # author aclweb url
        authors = dict((author_names[id], val) for id, val in authors.items())
        uni_authors[u] = sorted(list(authors.items()), key=lambda k_v: (k_v[1][0], k_v[1][2], k_v[1][1]), reverse=True)


    rank['authors'] = rank['domain'].map(uni_authors)


    return rank, author_rank, uni_authors



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
    # authors,maxYear = get_author_dict(3,3,3,3,3,2,2,2,2,1)
    # rank1,rank2,list1 = ranking(authors, 2010, 2019, 100)
    app.run(debug=True, use_debugger=False, use_reloader=False, passthrough_errors=True)