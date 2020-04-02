from flask import Flask, request, render_template, redirect
import json
from collections import defaultdict
import pandas as pd
import boto3
from datetime import datetime

from bokeh.models import LogColorMapper, ColumnDataSource, FactorRange, Legend
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.palettes import Set2_5
from bokeh.transform import factor_cmap

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    s3 = boto3.resource('s3', region_name='us-east-2')

    if request.method == 'POST':
        # journal
        CL = int(request.form['CL'])
        TACL = int(request.form['TACL'])

        # conference
        ACL_C = int(request.form['ACL-C'])
        NAACL_C = int(request.form['NAACL-C'])
        EMNLP_C = int(request.form['EMNLP-C'])
        CoNLL_C = int(request.form['CoNLL-C'])
        EACL_C = int(request.form['EACL-C'])
        COLING = int(request.form['COLING'])
        IJCNLP = int(request.form['IJCNLP'])

        # workshop or demo
        WKSPDEMO = int(request.form['WKSPDEMO'])

        startYear = int(request.form['start-year'])
        endYear = int(request.form['end-year'])

        num_uni = int(request.form['num_uni'])
        num_author = int(request.form['num_author'])

        # storing log info to s3
        ip = request.remote_addr
        info = [ip, startYear, endYear, num_uni, num_author,
                CL, TACL, ACL_C, NAACL_C, EMNLP_C, CoNLL_C, EACL_C, COLING,IJCNLP, WKSPDEMO]
        data = ','.join(map(str, info))

        filename = 'log/' + str(datetime.utcnow()) + '.txt'
        object = s3.Object('nlprankings', filename)
        object.put(Body=data)

        authors, maxYear = get_author_dict(
            CL, TACL, ACL_C, NAACL_C, EMNLP_C, CoNLL_C, EACL_C, COLING, IJCNLP, WKSPDEMO
        )

        rank1, rank2, uni_authors, scores = ranking(authors, startYear, endYear)
        rank1 = rank1.head(n=num_uni)
        rank1.index = rank1.index + 1
        rank2 = rank2.head(n=num_author)

        weights = [CL, TACL, ACL_C, NAACL_C, EMNLP_C, CoNLL_C, EACL_C, COLING, IJCNLP, WKSPDEMO]

        years = list(range(2010, maxYear + 1))

        # us map
        plot = create_us_state_map(scores)
        script, div = components(plot)  # Embed plot into HTML via Flask Render


        return render_template('home.html', ranking1=rank1, ranking2=rank2, year=[startYear, endYear],
        years=years, weights=list(map(int, weights)), num=[num_uni, num_author], uni_authors=uni_authors,
        script=script, div=div)

    else:

        authors,maxYear = get_author_dict(3,3,3,3,3,2,2,2,2,1)

        rank1,rank2,uni_authors,scores = ranking(authors, 2010, maxYear)
        rank1 = rank1.head(n=100)
        rank1.index = rank1.index + 1
        rank2 = rank2.head(n=100)

        years = list(range(2010, maxYear+1))


        # storing log info to s3
        ip = request.remote_addr
        info = [ip, 2010, maxYear, 100, 100, 3, 3, 3, 3, 3, 2, 2, 2, 2, 1]
        data = ','.join(map(str, info))

        filename = 'log/' + str(datetime.utcnow()) + '.txt'
        object = s3.Object('nlprankings', filename)
        object.put(Body=data)

        # us map
        plot = create_us_state_map(scores)
        script, div = components(plot)  # Embed plot into HTML via Flask Render



        return render_template('home.html', ranking1=rank1, ranking2=rank2, year=[2010, maxYear], years=years,
        weights=[3,3,3,3,3,2,2,2,2,1], num=[100, 100], uni_authors=uni_authors, script=script, div=div)


@app.route('/articles/')
def articles():
    return render_template("articles.html");



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

    university_info = pd.read_json('../dat/university_domain_us.json', orient='records')

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





def ranking(authors, startYear, endYear):

    us_universities = pd.read_json('../dat/university_domain_us.json', orient='records')


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

    author_rank = pd.DataFrame(sorted(list(author_score.items()), key=lambda x: x[1], reverse=True),
                               columns=['author_id', 'Score'])
    author_rank['url'] = author_rank['author_id'].str[0] + '/' + author_rank['author_id']
    author_rank['Author'] = author_rank['author_id'].map(author_names)
    author_rank = author_rank.round(2)


    # uni rank
    us_universities['domain_id'] = us_universities['domain'].apply(lambda x: x[0]) # take first domain as key
    us_name = dict(zip(us_universities.domain_id, us_universities.name))

    rank = pd.DataFrame(sorted(list(uni_score.items()), key=lambda x: x[1], reverse=True), columns=['domain', 'Score'])
    rank = rank[rank['domain'].isin(us_name.keys())]
    rank = rank.round(2)

    state_scores = rank # use the same data for us_state map

    rank['Institution'] = rank['domain'].map(us_name)
    rank = rank.reset_index(drop=True)

    # rounding & sorting by individual author scores
    for u,authors in uni_authors.items():
        for author,v in authors.items():
            v[0] = round(v[0], 2)
            v[3] = author[0] + '/' + author   # author aclweb url
        authors = dict((author_names[id], val) for id, val in authors.items())
        uni_authors[u] = sorted(list(authors.items()), key=lambda k_v: (k_v[1][0], k_v[1][2], k_v[1][1]), reverse=True)


    rank['authors'] = rank['domain'].map(uni_authors)


    # us_map (score by states)
    us_states = dict(zip(us_universities.domain_id, us_universities.state))
    state_scores['State'] = rank['domain'].map(us_states)
    state_scores = state_scores.groupby('State').sum()
    state_scores = state_scores.round(2)
    state_scores = state_scores.reset_index()
    state_score_dict = dict(zip(state_scores.State, state_scores.Score))

    return rank, author_rank, uni_authors, state_score_dict




def create_us_state_map(scores):
    from bokeh.sampledata.us_states import data as states

    states = {
        code: states for code, states in states.items() if code not in ['AK', 'HI']
    }

    state_xs = [state["lons"] for state in states.values()]
    state_ys = [state["lats"] for state in states.values()]

    teal_palette = ['#ffffff', '#e0f2f1', '#b2dfdb', '#80cbc4', '#4db6ac', '#26a69a', '#009688', '#00897b', '#00796b',
                    '#00695c']

    state_names = [state['name'] for state in states.values()]
    state_scores = [scores[code] if code in scores.keys() else 0 for code in states.keys()]
    color_mapper = LogColorMapper(palette=teal_palette, low=0.01, high=max(scores.values()))

    data = dict(
        x=state_xs,
        y=state_ys,
        name=state_names,
        rate=state_scores,
    )

    TOOLS = "pan,wheel_zoom,reset,hover,save"

    p = figure(
        title="NLP Ranking Scores Across U.S. States", tools=TOOLS,
        x_axis_location=None, y_axis_location=None,
        sizing_mode="scale_width",
        plot_width=1100, plot_height=700,
        tooltips=[
            ("State", "@name"), ("Score", "@rate{0,0.00}")
        ])
    p.grid.grid_line_color = None
    p.hover.point_policy = "follow_mouse"

    p.patches('x', 'y', source=data,
              fill_color={'field': 'rate', 'transform': color_mapper},
              fill_alpha=0.7, line_color="black", line_width=0.5)

    return p

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


@app.route('/visualizations/', methods=['GET', 'POST'])
def visualizations():
    df = pd.read_csv('../dat/graph_data.csv')

    if request.method == 'POST':
        selected = request.form.getlist('selected-university')

        # journal
        CL = int(request.form['CL'])
        TACL = int(request.form['TACL'])

        # conference
        ACL_C = int(request.form['ACL-C'])
        NAACL_C = int(request.form['NAACL-C'])
        EMNLP_C = int(request.form['EMNLP-C'])
        CoNLL_C = int(request.form['CoNLL-C'])
        EACL_C = int(request.form['EACL-C'])
        COLING = int(request.form['COLING'])
        IJCNLP = int(request.form['IJCNLP'])

        # workshop or demo
        WKSPDEMO = int(request.form['WKSPDEMO'])

        df = get_dataset(df, CL, TACL, ACL_C, NAACL_C, EMNLP_C, CoNLL_C, EACL_C, COLING, IJCNLP, WKSPDEMO)

        df_c = df.groupby('university')['score'].sum().reset_index()
        df_c = df_c.sort_values(by='score', ascending=False).reset_index()
        df_c.index = df_c.index + 1
        choices = df_c.university.to_dict()


        # ----------------------visualizations-----------------------

        p1 = score_timeline(df, selected)
        p2 = numpub(df, selected)
        p3 = ratio_of_contribution(df, selected)
        p4 = avg_author_num(df, selected)
        p_label = selected_color_legend(selected)

        script1, div1 = components(p1)
        script2, div2 = components(p2)
        script3, div3 = components(p3)
        script4, div4 = components(p4)
        scriptL, divL = components(p_label)


        return render_template("visualizations.html", choices=choices,
                               weights=[CL, TACL, ACL_C, NAACL_C, EMNLP_C, CoNLL_C, EACL_C, COLING, IJCNLP, WKSPDEMO],
                               script1=script1, div1=div1, script2=script2, div2=div2, script3=script3, div3=div3,
                               script4=script4, div4=div4, scriptL=scriptL, divL=divL)

    else:
        df = get_dataset(df, 3, 3, 3, 3, 3, 2, 2, 2, 2, 1)

        df_c = df.groupby('university')['score'].sum().reset_index()
        df_c = df_c.sort_values(by='score', ascending=False).reset_index()
        df_c.index = df_c.index + 1
        choices = df_c.university.to_dict()

        selected = []

        # ----------------------visualizations-----------------------

        p1 = score_timeline(df, selected)
        p2 = numpub(df, selected)
        p3 = ratio_of_contribution(df, selected)
        p4 = avg_author_num(df, selected)
        p_label = selected_color_legend(selected)

        script1, div1 = components(p1)
        script2, div2 = components(p2)
        script3, div3 = components(p3)
        script4, div4 = components(p4)
        scriptL, divL = components(p_label)


        return render_template("visualizations.html", weights=[3,3,3,3,3,2,2,2,2,1], choices=choices,
                               script1=script1, div1=div1, script2=script2, div2=div2, script3=script3, div3=div3,
                               script4=script4, div4=div4, scriptL=scriptL, divL=divL)


def get_dataset(df, CL, TACL, ACL_C, NAACL_C, EMNLP_C, CoNLL_C, EACL_C, COLING, IJCNLP, WKSPDEMO):

    def get_score(venue, type, numAuthor):

        score = {'journal': 3, 'conference': 3, 'workshop': 1, 'demonstration': 1}

        if venue == 'CL':
            venue_score = CL
        elif venue == 'TACL':
            venue_score = TACL
        elif venue == 'ACL' and type == 'conference':
            venue_score = ACL_C
        elif venue == 'NAACL' and type == 'conference':
            venue_score = NAACL_C
        elif venue == 'EMNLP' and type == 'conference':
            venue_score = EMNLP_C
        elif venue == 'CoNLL' and type == 'conference':
            venue_score = CoNLL_C
        elif venue == 'EACL' and type == 'conference':
            venue_score = EACL_C
        elif venue == 'COLING':
            venue_score = COLING
        elif venue == 'IJCNLP':
            venue_score = IJCNLP
        elif venue in ['workshop', 'demonstration']:
            venue_score = WKSPDEMO
        else:
            venue_score = score[type]

        return 1 / numAuthor * venue_score

    df['score'] = df.apply(lambda x: get_score(x.venue, x.type, x.numAuthor), axis=1)

    return df

# stacked bar chart
def score_timeline(df, selected):

    df = df[df['university'].isin(selected)]
    df = df.groupby(['authorID', 'university', 'year'])['score'].sum().reset_index()
    df['90th'] = df.groupby(['university', 'year'])['score'].transform(lambda x: x.quantile(.9))
    df['top10'] = df['score'] >= df['90th']
    df['s_score'] = df.groupby(['university', 'year', 'top10'])['score'].transform('sum')
    df = df[['university', 'year', 'top10', 's_score']].drop_duplicates()


    def getColumnDataSource(df, selected):

        years = list(range(2010, 2020))
        factors = [(x, y) for x in years for y in selected]



        others = df[df['top10'] == False].set_index(['year', 'university']).to_dict()['s_score']
        top10 = df[df['top10']==True].set_index(['year', 'university']).to_dict()['s_score']
        labels = selected * len(years)


        source = ColumnDataSource(data=dict(
            x=factors,
            others=[others[f] if f in others.keys() else 0 for f in factors],
            top10=[top10[f] if f in top10.keys() else 0 for f in factors],
            labels=labels,
        ))

        return source,factors

    def make_plot(source, factors, selected):

        categories = ['others', 'top10']

        factors = [tuple(str(x) for x in tup) for tup in factors]

        TOOLS = "pan,wheel_zoom,reset,hover,save"

        p = figure(x_range=FactorRange(*factors),
                   plot_height=400, plot_width=800,
                   title="University Score Timeline",
                   tools=TOOLS,
                   tooltips = [("University", "@labels"), ("Top10% Score", "@top10{0,0.00}"), ("Others Score", "@others{0,0.00}")]
                   )

        v = p.vbar_stack(categories, x='x', width=0.9,
                     source=source,
                     line_color=None,
                     fill_alpha=[1, 0.6],
                     fill_color=factor_cmap('x', palette=Set2_5, factors=selected, start=1, end=2))

        p.y_range.start = 0
        p.x_range.range_padding = 0.1
        p.xaxis.major_label_text_font_size = '0pt'
        p.xgrid.grid_line_color = None

        p.hover.point_policy = "follow_mouse"

        legend1 = Legend(items=[
            ("by top10%", [v[1]]),
            ("others", [v[0]]),
        ], location='center',
        label_width=30
        )

        p.add_layout(legend1, 'right')

        return p


    source,factors = getColumnDataSource(df, selected)


    return make_plot(source, factors, selected)


def numpub(df, selected):

    df = df[df['university'].isin(selected)]
    df = df.groupby(['authorID', 'university']).size().reset_index(name='pubCounts')
    df['numPub'] = df.pubCounts.apply(lambda x: '1' if x==1 else '2' if x==2 else '3 or more')
    df = df.groupby(['university', 'numPub']).size().reset_index(name='count')


    def getColumnDataSource(df, selected):

        one = df[df['numPub'] == '1'].set_index('university').to_dict()['count']
        two = df[df['numPub'] == '2'].set_index('university').to_dict()['count']
        three = df[df['numPub'] == '3 or more'].set_index('university').to_dict()['count']

        source = {'university': selected,
                'one': [one[s] if s in one.keys() else 0 for s in selected],
                'two': [two[s] if s in two.keys() else 0 for s in selected],
                'three': [three[s] if s in three.keys() else 0 for s in selected]}


        return source

    def make_plot(source, selected):

        num = ['one', 'two', 'three']
        TOOLS = "pan,wheel_zoom,reset,hover,save"

        p = figure(x_range=selected,
                   plot_height=400, plot_width=800,
                   title="Number of Authors in Various Publication Amount",
                   tools=TOOLS,
                   tooltips=[("University", "@university"), ("one", "@one"),("two", "@two"),("three or more", "@three")]
                   )

        v = p.vbar_stack(num, x='university', width=0.6,
                     source=source,
                     line_color=None,
                     fill_alpha=[1, 0.7, 0.4],
                     fill_color=factor_cmap('university', palette=Set2_5, factors=selected)
                     )

        p.y_range.start = 0
        p.x_range.range_padding = 0.1
        p.xaxis.major_label_text_font_size = '0pt'
        p.xgrid.grid_line_color = None
        p.yaxis.axis_label = "Number of Authors"
        p.yaxis.axis_label_text_font_style = "normal"
        p.xaxis.axis_label = "Universities"
        p.xaxis.axis_label_text_font_style = "normal"
        p.axis.minor_tick_line_color = None
        p.outline_line_color = None


        p.hover.point_policy = "follow_mouse"

        legend1 = Legend(title="# of pub per authors",
            items=[
            ("one", [v[1]]),
            ("two", [v[0]]),
            ("three or more", [v[0]]),
        ], location='center',
            label_width=30
        )

        p.add_layout(legend1, 'right')

        return p


    source = getColumnDataSource(df,selected)


    return make_plot(source,selected)


# avg or median
def ratio_of_contribution(df, selected):

    df = df.groupby(['university', 'pubID', 'year', 'numAuthor']).size().reset_index(name='AuthorCount')
    df['contribution'] = df.apply(lambda x: x.AuthorCount / x.numAuthor, axis=1)
    df = df.groupby(['university','year']).agg({'pubID': 'size', 'contribution': 'mean'}).\
        rename(columns={'pubID': 'count', 'contribution': 'mean_contribution'}).reset_index()



    def getColumnDataSource(df, selected):

        df = df[df['university'].isin(selected)]

        years = list(range(2010, 2020))

        x = [years] * len(selected)

        dict_data = df.set_index(['university','year']).to_dict()

        y = []
        for uni in selected:
            mean_contribution_value = []
            for year in years:
                try:
                    mean_contribution_value.append(dict_data['mean_contribution'][(uni, year)])
                except:
                    mean_contribution_value.append(0)


            y.append(mean_contribution_value)


        source = ColumnDataSource(data=dict(
            xs=x,
            ys=y,
            university=selected,
            color=Set2_5[:len(selected)],
        ))


        return source

    def make_plot(source, selected):


        TOOLS = "pan,wheel_zoom,reset,hover,save"

        p = figure(plot_height=400, plot_width=800,
                   title="Average Publication Percent Contribution Overtime",
                   tools=TOOLS,
                   tooltips=[("University", "@university"), ("year", "$data_x"), ("score", "$data_y")]
                   )

        p.multi_line(xs='xs', ys='ys', source=source, line_color='color')


        p.xaxis[0].ticker.desired_num_ticks = 10
        p.xaxis.axis_label = "Years"
        p.xaxis.axis_label_text_font_style = "normal"
        p.yaxis.axis_label = "Contribution Percentage"
        p.yaxis.axis_label_text_font_style = "normal"
        p.xgrid.grid_line_color = None

        return p

    source = getColumnDataSource(df, selected)


    return make_plot(source,selected)


def avg_author_num(df, selected):

    df = df[['university','pubID','numAuthor','year']].drop_duplicates()
    df = df.groupby(['university','year'])['numAuthor'].mean().reset_index()

    def getColumnDataSource(df, selected):

        df = df[df['university'].isin(selected)]

        years = list(range(2010, 2020))

        x = [years] * len(selected)

        dict_data = df.set_index(['university','year']).to_dict()

        y = []
        for uni in selected:
            mean_numAuthor = []
            for year in years:
                try:
                    mean_numAuthor.append(dict_data['numAuthor'][(uni, year)])
                except:
                    mean_numAuthor.append(0)


            y.append(mean_numAuthor)


        source = ColumnDataSource(data=dict(
            xs=x,
            ys=y,
            university=selected,
            color=Set2_5[:len(selected)],
        ))


        return source

    def make_plot(source, selected):

        TOOLS = "pan,wheel_zoom,reset,hover,save"

        p = figure(plot_height=400, plot_width=800,
                   title="Average Number of Authors per Publication Overtime",
                   tools=TOOLS,
                   tooltips=[("University", "@university"), ("year", "$data_x"), ("score", "$data_y")]
                   )

        p.multi_line(xs='xs', ys='ys', source=source, line_color='color')


        p.xaxis[0].ticker.desired_num_ticks = 10
        p.xaxis.axis_label = "Years"
        p.xaxis.axis_label_text_font_style = "normal"
        p.yaxis.axis_label = "Avg. Number of Authors"
        p.yaxis.axis_label_text_font_style = "normal"
        p.xgrid.grid_line_color = None

        return p

    source = getColumnDataSource(df, selected)


    return make_plot(source,selected)

def selected_color_legend(selected):

    empty = False
    if selected == []:
        empty = True
        selected = ['']

    height = 20 + len(selected) * 40

    p = figure(toolbar_location=None, plot_width=400, plot_height=height)

    if empty:
        p.square(x=0, y=0, size=0, color="white", legend_label='Please choose up to 5 universities')
    else:
        for i in range(len(selected)):
            p.square(x=0, y=0, size = 0, color=Set2_5[i], legend_label=selected[i])

    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.axis.visible = False

    p.legend.location = "center"

    return p


if __name__ == '__main__':
    # authors,maxYear = get_author_dict(3,3,3,3,3,2,2,2,2,1)
    # rank1,rank2,list1,score = ranking(authors, 2010, 2019)
    app.run(debug=True, use_debugger=False, use_reloader=False, passthrough_errors=True)