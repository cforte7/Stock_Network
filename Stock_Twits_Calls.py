import numpy as np
import pandas as pd
import requests
import json
import matplotlib.pyplot as plt
import networkx as nx
import datetime
import itertools

ticker_example = input('Please enter ticker to look up:\n').upper()
call_count = input('Please enter number of sets of 30 tweets to download: (Reccommended 10)\n')
add_node_count = int(input('Please enter max number of nodes off of the '+ticker_example+' node:\n'))
save_flag = ''

while save_flag not in ['y','n']:
    save_flag = input('Would you like to save API data as a Pandas DataFrame? y/n\n').lower()

#Import Pandas Dataframe of Company information saved from Nasdaq site - for future features
company_info = pd.read_pickle('C:\\Users\\Christopher Forte\\Documents\\Coding\\Stock_Network\\company_data.pickle')

#Initialization to set max_id for API Calls
def get_current_max(symbol):
    url_base = 'https://api.stocktwits.com/api/2/streams/symbol/' + str(symbol) + '.json?limit=1'
    init_call = requests.get(url_base)
    init_call = json.loads(init_call.text)
    max_id = str(init_call['messages'][0]['id'])
    return(max_id)


df_columns = ['stock_id','body','created_at','tweet_id','symbols']
tweet_container = []  #list of lists to be made into pd.DataFrame
used_tweets = []

#Function to generate link to call API
def generate_api_link(symbol):
    url_base = 'https://api.stocktwits.com/api/2/streams/symbol/'+str(symbol)+'.json?max='+max_id+'&limit=30'
    return url_base

#Function to call API and store set of tweets
def twit_api_call(symbol):
    tweet_temp = []
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
        if tweet_id not in used_tweets:
            tweet_temp.append([symbol_called,tweet_body,tweet_time,tweet_id,tweet_symbols]) #add row to list
    max_id = str(api_json['messages'][-1]['id'])#Oldest tweet called, used as parameter in next call to set time range
    return tweet_temp, max_id

max_id = get_current_max(ticker_example)
initial_max = max_id

#Initial set of calls for root node
for x in range(int(call_count)):
    tweet_add, max_id = twit_api_call(ticker_example)
    tweet_container = tweet_container+tweet_add

current_time = str(datetime.datetime.now().strftime('%d_%m_%y_%H_%M')) #Get current date/time for unique filenames
tweetFrame = pd.DataFrame(data=tweet_container,columns=df_columns)
used_tweets = used_tweets+list(tweetFrame.tweet_id)

if save_flag == 'y':
    pd.to_pickle(tweetFrame,'Tweet_Frame_'+current_time+'.pickle') #export DataFrame if user designated



#construct matrix of mentions as well as dictionaries of companies within API call
def mention_construct(frame,ticker_called):
    tweet_symbols = np.array(frame.symbols)
    mentions = filter(lambda x: len(x) > 1, tweet_symbols)
    mentions = list(mentions)


    #Create dictionarys to link matrix index to stock symbol and vice versa
    symbol_index = {}
    unique_symbols = np.unique([ticker for innerlist in mentions for ticker in innerlist])
    for x in unique_symbols:
        symbol_index[x] = len(symbol_index)
    index_symbol = dict([(value,key) for key,value in symbol_index.items()])

    mention_size = len(unique_symbols)
    mention_matrix = np.zeros((mention_size,mention_size))

    for x in mentions:
        tweet_combos = list(itertools.combinations(x,2))
        for y in tweet_combos:
            index_one = symbol_index[y[0]]
            index_two = symbol_index[y[1]]
            mention_matrix[index_one,index_two] += 1
            mention_matrix[index_two, index_one] += 1


    ticker_index = symbol_index[ticker_called]
    return mention_matrix[ticker_index,:],symbol_index,index_symbol


root_indicies,symbol_index,index_symbol = mention_construct(tweetFrame,ticker_example)





#Extract most mentioned companies for root company
candidate_count = sum(root_indicies>=1)
if candidate_count <= add_node_count:
    root_indicies = root_indicies.argsort()[-candidate_count:][::-1]
else:
    root_indicies = root_indicies.argsort()[-add_node_count:][::-1]

network_tickers = []
G = nx.Graph()
G.add_node(str(ticker_example))
node_labels = []

#Construct graph from main stock node
for x in root_indicies:
    network_tickers.append(index_symbol[x])
    G.add_node(index_symbol[x])
    G.add_edge(ticker_example,index_symbol[x])

#API Calls for companies connected to root nodes
for x in network_tickers:
    max_id = initial_max
    secondary_container = []
    for y in range(3):
        tweet_add, max_id = twit_api_call(x)
        secondary_container = secondary_container+tweet_add
    secondary_Frame = pd.DataFrame(data=secondary_container,columns=df_columns)
    secondary_roots,symbol_index,index_symbol = mention_construct(secondary_Frame,x)
    secondary_roots = secondary_roots.argsort()[-3:][::-1]
    for z in secondary_roots:
        G.add_edge(x,index_symbol[z])


#Draw graph
graph_pos = nx.spring_layout(G)
nx.draw_networkx_nodes(G, graph_pos, node_size=5000, node_color='blue', alpha=0.3)
nx.draw_networkx_edges(G, graph_pos)
nx.draw_networkx_labels(G, graph_pos, font_size=9, font_family='sans-serif')

#Save network diagram and show image
plt.savefig(current_time+'_network_image.png')
plt.show()
