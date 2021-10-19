import csv
import json
import math
import pandas as pd
import requests
import sys

def getUserId(username):
  url = "https://www.speedrun.com/api/v1/users?name=" + username
  data = requests.get(url).json()['data']
  if len(data) > 0:
    for u in data:
      if u['names']['international'] == username:
        return u['id']
  print(data)
  raise Exception('Searched for ' + username + ', got back ' + str(len(data)) + ' entries (expected 1)') 

def getPBs(userid, all = False):
  url = "https://www.speedrun.com/api/v1/users/" + userid + "/personal-bests?embed=game,category,region,platform,players"
  data = requests.get(url).json()['data']
  pbdf = pd.DataFrame(data)
  pbdf = pbdf.join(pbdf['run'].apply(pd.Series), rsuffix='run')
  pbdf.drop(axis=1, columns=['run'], inplace=True)
  if all:
    allurl = "https://www.speedrun.com/api/v1/runs?user=" + userid + "&embed=game,category,region,platform,players"
    data = requests.get(allurl).json()['data']
    alldf = pd.DataFrame(data)
    alldf['place'] = math.nan
    pbdf = pbdf.append(alldf)
    return pbdf
  return pbdf

def getPlayers(x):
  players = []
  for p in x.players['data']:
    players.append(p['names']['international']) 
  return ", ".join(players)

def getRegion(x):
  if x.region['data'] == []:
    return None
  else:
    return x.region['data']['name']

def getPlatform(x):
  if x.platform['data'] == []:
    return None
  else:
    return x.platform['data']['name']

varMemo = {}
def getVariable(variableid):
  if variableid not in varMemo:
    url = "https://www.speedrun.com/api/v1/variables/" + variableid
    response = requests.get(url)
    varMemo[variableid] = response.json()['data']
  return varMemo[variableid]

def getValue(variableid, valueid):
  var = getVariable(variableid)
  return var['values']['values'][valueid]['label']

def getVariables(x, subcats):
  if x['values'] == {}:
    return None
  else:
    variables = []
    for varid, valid in x['values'].items():
      if getVariable(varid)['is-subcategory'] == subcats:
        variables.append(getValue(varid, valid))  
      retval = " -- ".join(variables)
    return retval

def getVideo(x):
  if 'links' in x and len(x['links']) > 0:
    return x['links'][0]['uri']
  else:
    return None
    
if len(sys.argv) != 3:
  print(sys.argv[0] + ": export your SRC PBs to a csv file")
  print()
  print("Usage: python " + sys.argv[0] + " <SRC user name> <output csv filename>" )
  exit(-1)

username = sys.argv[1]
outfilename = sys.argv[2]
userid = getUserId(username)
rawdf = getPBs(userid, all=True)

runsdf = pd.DataFrame()
runsdf['place'] = rawdf['place']
runsdf['game'] = rawdf.apply(lambda x: x.game['data']['names']['international'], axis=1)
runsdf['category'] = rawdf.apply(lambda x: x.category['data']['name'], axis=1)
runsdf['subcategory(s)'] = rawdf.apply(lambda x: getVariables(x, True), axis=1)
runsdf['variable(s)'] = rawdf.apply(lambda x: getVariables(x, False), axis=1)
runsdf['platformname'] = rawdf.apply(lambda x: getPlatform(x), axis=1)
runsdf['regionname'] = rawdf.apply(lambda x: getRegion(x), axis=1)
runsdf['players'] = rawdf.apply(lambda x: getPlayers(x), axis=1)
runsdf['time'] = rawdf.apply(lambda x: x['times']['primary_t'], axis=1)
runsdf['date'] = rawdf.apply(lambda x: x['date'], axis=1)
runsdf['video'] = rawdf.apply(lambda x: getVideo(x['videos']), axis=1)
runsdf['comment'] = rawdf.apply(lambda x: str(x['comment']).replace('\n', ' ').replace('\r', ' ') , axis=1)

runsdf.to_csv(outfilename, index=False, quoting=csv.QUOTE_NONNUMERIC)
print(username, "PBs exported to", outfilename)

