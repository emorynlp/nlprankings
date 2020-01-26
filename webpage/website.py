from flask import Flask, request, render_template, redirect
import json
from collections import defaultdict
import pandas as pd
import boto3
from dynamodb_json import json_util


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':

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
    # dynamodb = boto3.resource('dynamodb', 'us-east-2')
    #
    # table_uni = dynamodb.Table('university')
    # response_uni = table_uni.scan()
    # data_uni = response_uni['Items']
    # university = pd.DataFrame(json_util.loads(data_uni))

    # table_bib = dynamodb.Table('bibmap')
    # response_bib = table_bib.scan()
    # data_bib = response_bib['Items']
    # bibmap = pd.DataFrame(json_util.loads(data_bib))


    university = pd.read_json('../data-collection/university.json', orient='records')
    bibmap = json.load(open('../data-collection/bibmap.json'))

    venue_pub = {}  # only look at publications with authors from an university institution
    for pub_id in [y[0] for x in university['publications'].values.tolist() if x for y in x]:
        venue = find_venue(pub_id)
        if venue in venue_pub.keys():
            venue_pub[venue].append(pub_id)
        else:
            venue_pub[venue] = [pub_id]

    # scoring each venue type
    score = {'journal': 3, 'conference': 3, 'workshop': 1, 'demonstration': 1}

    # authors = {author_id: {university1_domain: {2019: [score, num_pub], 2018: [score, num_pub]}}}
    authors = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0,0])))
    maxYear = 2010 # take the latest year in the data (initialize at 2010, which is the earliest year)

    for k, v in venue_pub.items():
        bib = next((y for y in bibmap if y['id'] == k), None)
        with open('../data-collection/pub_json/' + k + '.json') as p:
            json_file = json.load(p)

            # customized scoring weights
            if 'J' in k:
                venue_score = CL
            elif 'Q' in k:
                venue_score = TACL
            elif 'P' in k and bib['type'] == 'conference':
                venue_score = ACL_C
            elif 'N' in k and bib['type'] == 'conference':
                venue_score = NAACL_C
            elif 'D' in k and bib['type'] == 'conference':
                venue_score = EMNLP_C
            elif 'K' in k and bib['type'] == 'conference':
                venue_score = CoNLL_C
            elif 'E' in k and bib['type'] == 'conference':
                venue_score = EACL_C
            elif 'C' in k:
                venue_score = COLING
            elif 'I' in k:
                venue_score = IJCNLP
            elif bib['type'] in ['workshop', 'demonstration']:
                venue_score = WKSPDEMO
            else:
                venue_score = score[bib['type']]

            for pub in [x for x in json_file if x['id'] in v]:
                for i in range(len(pub['authors'])):
                    if '.edu' == pub['emails'][i][-4:]:
                        author_id = pub['author_id'][i]
                        year = pub['year']
                        if int(year) > maxYear:
                            maxYear = int(year)
                        uni_domain = parse_email(pub['emails'][i].split('@')[1])
                        if uni_domain == 'uw.edu': # university of washington has 2 domains (washington.edu & uw.edu)
                            uni_domain = 'washington.edu'
                        if uni_domain == 'iub.edu': # indiana university bloomington (2 domains)
                            uni_domain = 'indiana.edu'
                        pages = pub['pages'].split('--')
                        if len(pages) > 1:
                            num_pages = int(pages[1]) - int(pages[0]) + 1
                            if num_pages > 5:
                                #score
                                authors[author_id][uni_domain][year][0] += 1 / len(pub['authors']) * venue_score
                                #num of publications
                                authors[author_id][uni_domain][year][1] += 1

    return authors,maxYear





def ranking(authors, startYear, endYear, top_k):

    uni_score = {} # university score rank
    author_score = {}  # author score rank
    # uni_authors = {uni: {author1: [score, num_pub, last_year_pub, href], author2: [score, num_pub, last_year_pub, href]}}
    uni_authors = defaultdict(lambda: defaultdict(lambda: [0, 0, 0, 0]))  # authors in each university, score + num_pub
    for author, institutions in authors.items():
        for institution, years in institutions.items():
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
    author_info = pd.read_json('../data-collection/author.json', orient='records')
    author_info['firstname'] = author_info.firstname.fillna('')
    author_info['name'] = author_info['firstname'] + ' ' + author_info['lastname']
    author_names = dict(zip(author_info.author_id, author_info.name))

    author_rank = pd.DataFrame(sorted(list(author_score.items()), key=lambda x: x[1], reverse=True)[:top_k],
                               columns=['author_id', 'Score'])
    author_rank['url'] = author_rank['author_id'].str[0] + '/' + author_rank['author_id']
    author_rank['Author'] = author_rank['author_id'].map(author_names)
    author_rank = author_rank.round(2)


    # uni rank
    us_universities = pd.read_csv('../data-collection/us_universities.tsv', sep='\t', names=['name', 'domain', 'city', 'state'])

    us_name = dict(zip(us_universities.domain, us_universities.name))

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
    if 'W' in pub_id:
        return pub_id[:-2]
    else:
        return pub_id[:-3]



if __name__ == '__main__':
    # authors,maxYear = get_author_dict(3,3,3,3,3,2,2,2,2,1)
    # print(authors)
    # rank1,rank2,list1 = ranking(authors, 2010, 2019, 100)
    # print(len(rank1.Institution.unique()))
    # print(len(rank1['Institution']))
    # author_ranking(authors, 2010, 2019, 100)
    app.run(debug=True, use_debugger=False, use_reloader=False, passthrough_errors=True)
