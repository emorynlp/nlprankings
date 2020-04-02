import boto3
import pandas as pd
import numpy as np

# user analysis
def get_user_log():

    s3 = boto3.resource('s3', region_name='us-east-2')
    bucket = s3.Bucket('nlprankings')


    logs = pd.DataFrame(columns=['datetime','IP','startYear','endYear','num_uni','num_author','CL','TACL','ACL_C','NAACL_C','EMNLP_C',
                                 'CoNLL_C','EACL_C','COLING','IJCNLP','WKSPDEMO'])

    access_num = 0
    for obj in bucket.objects.filter(Prefix="log/"):
        if '.txt' in obj.key:
            datetime = obj.key[4:-4]
            body = obj.get()['Body'].read()
            log_info = body.decode("utf-8").split(',')

            if len(log_info) > 14:
                s = pd.Series([datetime] + log_info, index=logs.columns)
                logs = logs.append(s, ignore_index=True)

                access_num += 1
                print(access_num)


    logs.to_csv('../dat/log_info.csv')

def user_analysis(logs):

    logs['date'] = logs.datetime.apply(lambda x: x.split(' ')[0])

    print(len(logs)) # num of accesses
    # print(logs.date.nunique()) # num of dates
    # print(logs.IP.nunique()) # num of uniq IP
    #
    # # timeframe checked
    # print(logs.groupby(['startYear', 'endYear']).size())  # .reset_index(name='pubCounts')
    #
    # # weights
    # for l in logs.groupby(['CL','TACL','ACL_C','NAACL_C','EMNLP_C','CoNLL_C',
    #                        'EACL_C','COLING','IJCNLP','WKSPDEMO']).size().reset_index(name='Counts').values.tolist():
    #     print(l)

    uniq_access = logs.groupby(['IP', 'date']).size().reset_index(name='count')


    re_access = uniq_access.groupby('IP').size().reset_index(name='count')
    re_access = re_access[re_access['count'] <= 15]
    print(re_access)
    re_access_count = re_access.groupby('count').size().reset_index(name='users')
    re_access_count['percent'] = re_access_count.users.apply(lambda x: x/1219)
    print(re_access_count)

    plt.figure(figsize=(15,10))
    plt.hist(re_access['count'], bins=15)
    plt.ylabel('count', fontsize=12)
    plt.xlabel('number of re-visits', fontsize=12)
    plt.show()



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


from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
import matplotlib.pyplot as plt

def university_trend_clustering(df):

    trend_df = df.groupby(['university', 'year'])['score'].sum().reset_index()
    trend_df = trend_df.pivot(index='university',columns='year',values='score')
    trend_df = trend_df.fillna(0)

    trend_df.columns.name = None

    Z = linkage(trend_df, 'ward')

    plt.figure(figsize=(40,60))
    plt.xlabel('distance')
    dendrogram(Z, orientation='right', labels=trend_df.index, leaf_font_size=12)
    plt.show()

    # k=3
    # clusters = fcluster(Z, k, criterion='maxclust')
    # clusters = list(clusters)
    #
    #
    # trend_df['total'] = trend_df.sum(axis=1)
    # trend_df['rank'] = trend_df['total'].rank(ascending=False)
    # trend_df['cluster'] = clusters

    # print(trend_df)


    # print(trend_df[(trend_df['cluster'] == 1) & (trend_df['rank'] < 30)]['rank'])
    #
    # print(clusters.count(1))

    # c1 = ['University of Maryland', 'University of California, Berkeley',
    #       'University of Illinois at Urbana-Champaign', 'Information Sciences Institute']
    #
    # pub2016 = df[(df['university'].isin(c1)) & (df['year'] == 2016) & (~df['type'].isin(['workshop', 'demonstration']))]
    #
    #
    #
    # for p in pub2016.values.tolist():
    #     # print(p)
    #     with open('../dat/acl_anthology/json/'+p[4]+'.json') as f:
    #         pub = pd.read_json(f).set_index('id')
    #         records = pub.to_dict()
    #         print(p[-2],records['title'][p[3]])



    # trend_df = trend_df.reset_index()
    #
    # c1_df = trend_df[trend_df['university'].isin(c1)]
    #
    # c1_df = c1_df.drop(columns=['total', 'rank', 'cluster'])
    # c1_df = c1_df.set_index('university').T
    # c1_df = c1_df.reset_index()
    #
    # # print(c1_df.columns)
    #
    # palette = plt.get_cmap('Set1')
    #
    # num = 0
    # plt.figure()
    # for column in c1_df.drop(columns=['index'], axis=1):
    #     num += 1
    #     plt.plot(c1_df['index'], c1_df[column], marker='', color=palette(num), linewidth=1, alpha=0.9, label=column)
    #
    # # Add legend
    # plt.legend(ncol=2, loc='upper center', bbox_to_anchor=(0.5, -0.15))
    #
    # # Add titles
    # plt.xlabel("Year")
    # plt.ylabel("Score")
    # plt.xticks(np.arange(2010,2020))
    # plt.show()

    return

def find_venue(pub_id):
    if 'W' in pub_id or 'D19-5' in pub_id or 'D19-6' in pub_id:
        return pub_id[:-2]
    else:
        return pub_id[:-3]

from matplotlib.ticker import MaxNLocator

def university_attended(df, k):

    df = df.drop(columns=['Unnamed: 0'])

    df_author = df.groupby('authorID')['score'].sum().reset_index()
    df_author = df_author.sort_values(by='score', ascending=False)
    df_author = df_author.head(n=k)

    topk_authors = df_author['authorID'].tolist()


    df = df[df['authorID'].isin(topk_authors)]
    df = df.groupby(['authorID', 'university']).size().reset_index(name='count')
    df = df.groupby('university').size().reset_index(name='count')
    df = df.sort_values(by='count', ascending=False).reset_index()
    df = df.drop(columns=['index'])

    print(df)

    plt.figure(figsize=(20,10))
    height = df['count']
    bars = df['university']
    y_pos = np.arange(len(bars))

    plt.barh(y_pos, height)

    # Create names on the y-axis
    plt.yticks(y_pos, bars)
    plt.xlabel('Count')
    plt.gca().invert_yaxis()
    plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))

    # Show graphic
    plt.show()

    return


def ranking_overtime(df, k):

    topk_u = df.groupby('university')['score'].sum().reset_index()
    topk_u = topk_u.sort_values(by='score', ascending=False)
    topk_u = topk_u.head(n=k).reset_index()
    top = topk_u.university.tolist()

    df = df.groupby(['university', 'year'])['score'].sum().reset_index()
    df = df.pivot(index='university', columns='year', values='score')
    df = df.fillna(0)
    df.columns.name = None
    df = df.reset_index()

    df['total'] = df.sum(axis=1)

    for year in range(2010,2020):
        df[str(year) + '_Rank'] = df[year].rank(ascending=False)

    print(df)

    df = df[df['university'].isin(top)]

    df = df.drop(columns=list(range(2010,2020)))

    df = df.sort_values(by='total', ascending=False)

    df = df.drop(columns=['total'])

    df.loc[:, df.columns != 'university'] = df.loc[:, df.columns != 'university'].astype(int)


    df['2010-2019'] = df['2010_Rank'] - df['2019_Rank']


    for d in df.values.tolist():
        print(d)

    print(df['2010-2019'].mean())

    print(sum(sum([df['2010-2019'] < 0])))
    print(sum(sum([df['2010-2019'] > 0])))
    print(sum(sum([df['2010-2019'] == 0])))


def university_ranking(df):

    print(df.columns)

    df = df.groupby('university').agg({'authorID': 'nunique', 'score': 'sum'}).reset_index()
    df = df.sort_values(by='score', ascending=False)
    df = df.head(n=50)
    df = df.round(2)
    print(df)


def wc_index(df):

    top_nlp = df.groupby('authorID')['score'].sum().reset_index()
    top_nlp = top_nlp.sort_values(by='score', ascending=False)
    top_nlp = top_nlp.head(n=30).reset_index()

    # print(top_nlp['authorID'])


    df['index_count'] = df['score'] >= 1
    df['index_count'] = df['index_count'].astype(int)
    df = df[df['authorID'].isin(top_nlp['authorID'])]
    df = df.groupby(['authorID', 'year'])['index_count'].sum().reset_index()
    df = df[df['year'] >= 2015]
    df = df.pivot(index='authorID',columns='year',values='index_count')
    print(df)

    return



if __name__ == '__main__':
    # get_user_log()

    # logs = pd.read_csv('../dat/log_info.csv')
    # user_analysis(logs)

    df = pd.read_csv('../dat/graph_data.csv')
    df = get_dataset(df, 3, 3, 3, 3, 3, 2, 2, 2, 2, 1)

    # university_trend_clustering(df)
    # university_attended(df, 100) # by top k authors
    # ranking_overtime(df, 50)
    # university_ranking(df)
    wc_index(df)



