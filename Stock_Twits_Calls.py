import numpy as np
import pandas as pd
import requests
import json
from pprint import pprint
import matplotlib.pyplot as plt
import networkx as nx
import datetime
import itertools
ticker_example = input('Please enter ticker to look up:\n')
call_count = input('Please enter number of sets of 30 tweets to download:\n')
auth_url = 'https://api.stocktwits.com/api/2/oauth/authorize?client_id=e50c61fe18c4076b&response_type=token&redirect_uri=http://www.example.com'
url_base = 'https://api.stocktwits.com/api/2/streams/symbol/'
url_two = '.json?max='
count_url = '&limit=30'

#Import Pandas Dataframe of Company information saved from Nasdaq site
company_info = pd.read_pickle('C:\\Users\\Christopher Forte\\Documents\\Coding\\Stock_Network\\company_data.pickle')

def init_api(symbol):
    url_base = 'https://api.stocktwits.com/api/2/streams/symbol/' + str(symbol) + '.json?limit=1'
    init_call = requests.get(url_base)
    init_call = json.loads(init_call.text)
    max_id = str(init_call['messages'][0]['id'])
    return(max_id)


df_columns = ['stock_id','body','created_at','tweet_id','symbols']
tweet_container = []  #list of lists to be made into pd.DataFrame

def generate_api_link(symbol):
    url_base = 'https://api.stocktwits.com/api/2/streams/symbol/'+str(symbol)+'.json?max='+max_id+'&limit=30'
    return url_base

def twit_api_call(symbol):
    api_url = generate_api_link(symbol)
    api_call = requests.get(api_url)
    api_json = json.loads(api_call.text)
    symbol_called = api_json['symbol']['symbol']
    for y in api_json['messages']: #iterate through 'messages' entries that contain tweet data
        tweet_body = y['body']
        tweet_time = y['created_at']
        tweet_id = y['id']
        tweet_symbols = []
        for z in y['symbols']: #iterate through entries in 'symbols'
            tweet_symbols.append(z['symbol']) #append list with entry 'symbol' from 'symbols' entry
        tweet_container.append([symbol_called,tweet_body,tweet_time,tweet_id,tweet_symbols]) #add row to list
    max_id = str(api_json['messages'][-1]['id']) #Oldest tweet called, used as parameter in next call to set time range
max_id = init_api(ticker_example)
for x in range(call_count):
    twit_api_call(ticker_example)

tweetFrame = pd.DataFrame(data=tweet_container,columns=df_columns)
current_time = str(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'))
pd.to_pickle(tweetFrame,'Tweet_Frame.pickle')


tweetFrame = pd.read_pickle('Tweet_Frame.pickle')
tweet_symbols = np.array(tweetFrame.symbols)

#Extract entries that have more than one company mentioned
mentions = filter(lambda x: len(x) > 1, tweet_symbols)
mentions = list(mentions)


#Create dictionary to link matrix index to stock symbol
symbol_index = {}
unique_symbols = np.unique([ticker for innerlist in mentions for ticker in innerlist])
for x in unique_symbols:
    symbol_index[x] = len(symbol_index)


mention_size = len(unique_symbols)
mention_matrix = np.zeros((mention_size,mention_size))


for x in mentions:
    tweet_combos = list(itertools.combinations(x,2))
    for y in tweet_combos:
        indexer = [symbol_index[y[0]],symbol_index[y[1]]]
        row_index = min(indexer)
        column_index = max(indexer)
        mention_matrix[row_index,column_index] += 1

index_symbol = dict([(value,key) for key,value in symbol_index.items()])
print(symbol_index)
ticker_index = symbol_index[ticker_example]
G = nx.Graph()
G.add_node(str(ticker_example))
node_labels = []
for x in range(mention_matrix.shape[0]):
    if mention_matrix[ticker_index,x] >= 1:
        G.add_node(index_symbol[x])
        G.add_edge(ticker_example,index_symbol[x])

#graph_pos = nx.random_layout(G)
#nx.draw_networkx_nodes(G, graph_pos, node_size=5000, node_color='blue', alpha=0.3)
#nx.draw_networkx_edges(G, graph_pos)
#nx.draw_networkx_labels(G, graph_pos, font_size=9, font_family='sans-serif')

nx.draw_networkx(G)
plt.show()
