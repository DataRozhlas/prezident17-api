
# coding: utf-8

# In[1]:


import requests
import json
import xml.etree.ElementTree as ET
from time import gmtime, strftime, sleep
import time
import datetime
import boto3
from var import *

ns = '{http://www.volby.cz/prezident/}'
s3 = boto3.client('s3')


# In[2]:


kandidati = {
    '1': 'Mirek Topolánek',
    '2': 'Michal Horáček',
    '3': 'Pavel Fischer',
    '4': 'Jiří Hynek',
    '5': 'Petr Hannig',
    '6': 'Vratislav Kulhánek',
    '7': 'Miloš Zeman',
    '8': 'Marek Hilšer',
    '9': 'Jiří Drahoš'
}


# In[3]:


while True:
    now = str(datetime.datetime.utcnow().isoformat()) + 'Z'
    print(now)
    r = requests.get(endpoint + '/vysledky_zahranici?kolo=' + kolo)
    root = ET.fromstring(r.text)

    data = {'UPDATED': now}

    for kont in root[0].findall(ns + 'KONTINENT'):
        for stat in kont.findall(ns + 'STAT'):
            out = {'KAND': {}}
            stat_id = stat.attrib['ZKRATKA']
            out.update(stat.attrib)
            out.update(stat.find(ns + 'UCAST').attrib)
            
            for kn in stat.findall(ns + 'HODN_KAND'):
                kn_id = kn.attrib['PORADOVE_CISLO']

                out['KAND'][kn_id] = kn.attrib
                out['KAND'][kn_id].update({'JMENO': kandidati[kn.attrib['PORADOVE_CISLO']]})

            print(stat_id + ' | ' + strftime("%Y-%m-%d %H_%M_%S", time.localtime())) 
            putFile = s3.put_object(Bucket='prezident17', 
                            Key='kolo' + kolo + '/obce/' + stat_id + '.json', 
                            Body=json.dumps(out), 
                            ACL='public-read', 
                            ContentType='application/json')
    time.sleep(45)
