#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
import urllib.request
import requests
from http.cookiejar import CookieJar
import re
from bs4 import BeautifulSoup as bs
import pandas as pd
import datetime
from matplotlib import pyplot
import json
import base64
from io import BytesIO

TOTAL = 0
DISTANCE = 5
DAYS_BACK = 2
PLACES = []
START_DATE = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(DAYS_BACK), '%d.%m.%Y')
END_DATE = datetime.datetime.strftime(datetime.datetime.now(), '%d.%m.%Y')
df = pd.DataFrame(columns=['day','month','year','hour','minute', 'place'])
URL = 'http://www.oref.org.il//Shared/Ajax/GetAlarms.aspx?fromdate=' + START_DATE + '&todate=' + END_DATE

try:
    req=urllib.request.Request(URL, None, {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36','Accept-Encoding': 'gzip, deflate','Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7','Connection': 'keep-alive'})
    cj = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    response = opener.open(req)
    req=urllib.request.Request(URL, None)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    response = opener.open(req)
    page = bs(response.read())
    response.close()
except urllib.request.HTTPError as inst:
    output = format(inst)
    print(output)

alerts_parsed = page.find_all('li')
for alert in alerts_parsed:
    alert_l = []
    attrs = alert.findAll('span')
    for atr in attrs[0:2]:
        alert_l.append(re.findall('[0-9]{2}',str(atr)))
    alert_l.append(alert.findAll('span')[2].contents)
    alert_l = [j for i in alert_l for j in i]
    df = df.append(pd.DataFrame([alert_l],columns=['day','month','year','hour','minute', 'place']))
df['d_place'] = df.apply(lambda x: x['place'][::-1], axis = 1)

for place in df['place']:
    if ',' in place:
        place = place.split(',')[0]
    q = 'https://data.gov.il/api/action/datastore_search?resource_id=a5e7080d-3c37-49c2-8cd0-cb2724809216&q=' + place
    res = requests.get(q)
    try:
        pop = json.loads(res.content)['result']['records'][0]['סהכ']
        TOTAL += pop
    except:
        continue
    PLACES.append(place)

t = pd.Categorical(df['d_place']).value_counts()
t = t.sort_values(ascending=False)
t = t[0:]

fig, ax = pyplot.subplots(figsize = (20,10))
ax.bar(list(t.index), t.values)
fig.autofmt_xdate()
ax.set_title(START_DATE + ' - ' + END_DATE + '\nTOTAL ALARMS: ' + str(sum(t.values)), fontdict={'fontsize' : 20})
ax.tick_params(axis='both', labelsize=20)

tmpfile = BytesIO()
fig.savefig(tmpfile, format='png')
encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')

l1 = ('<center><font size=6>%s people ran %s kilometers in the past %s days...</font>' %(TOTAL,TOTAL*DISTANCE//1000,DAYS_BACK))
l2 = 'ב' + ', '.join(PLACES)
page = '''
<html>
<title>
Total Kilometers
</title>
<body><br><br><br><br>
''' + l1 + '''<br><font size=5 face=arial>'''  + l2 +  '''
<font></center>
<div>
  <center><img src=\"data:image/png;base64, ''' + encoded + '''\"/></center>
</div>
</body>
</html>
'''

page = page.replace('\n', '')

from IPython.display import HTML
HTML(page)
o = open('./index.html', 'w')
o.write(page)
o.close()
