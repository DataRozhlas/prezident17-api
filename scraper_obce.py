
# coding: utf-8

# In[1]:


import requests
import json
import xml.etree.ElementTree as ET
from time import gmtime, strftime, sleep
import time
import datetime
import boto3
from multiprocessing import Pool
from var import *


# In[3]:


kraje = {
    'CZ010': 'Hlavní město Praha',
    'CZ020': 'Středočeský kraj',
    'CZ031': 'Jihočeský kraj',
    'CZ032': 'Plzeňský kraj',
    'CZ041': 'Karlovarský kraj',
    'CZ042': 'Ústecký kraj',
    'CZ051': 'Liberecký kraj',
    'CZ052': 'Královéhradecký kraj',
    'CZ053': 'Pardubický kraj',
    'CZ063': 'Kraj Vysočina',
    'CZ064': 'Jihomoravský kraj',
    'CZ071': 'Olomoucký kraj',
    'CZ072': 'Zlínský kraj',
    'CZ080': 'Moravskoslezský kraj'
}


# In[4]:


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


# In[ ]:


ns = '{http://www.volby.cz/prezident/}'
s3 = boto3.client('s3')


# In[ ]:


def write(out):
    obid = out['CIS_OBEC']
    print(obid + ' | ' + strftime("%Y-%m-%d %H_%M_%S", time.localtime())) 
    putFile = s3.put_object(Bucket='prezident17', 
                            Key='kolo' + kolo + '/obce/' + obid + '.json', 
                            Body=json.dumps(out), 
                            ACL='public-read', 
                            ContentType='application/json')

while True:
    for kraj in kraje:
        print(kraje[kraj])
        kr_data = []
        now = str(datetime.datetime.utcnow().isoformat()) + 'Z'
        r = requests.get(endpoint + '/vysledky_kraj?kolo=&nuts=' + kraj)
        root = ET.fromstring(r.text)
        for okres in root[0].findall(ns + 'OKRES'):    
            for obec in okres.findall(ns + 'OBEC'):
                out = {
                    'UPDATED': now,
                    'OKRES': okres.attrib['NUTS_OKRES'],
                    'NAZ_OKRES': okres.attrib['NAZ_OKRES'],
                    'KAND': {}
                }
                out.update(obec.attrib)
                out.update(obec.find(ns + 'UCAST').attrib)
                
                for kn in obec.findall(ns + 'HODN_KAND'):
                    kn_id = kn.attrib['PORADOVE_CISLO']

                    out['KAND'][kn_id] = kn.attrib
                    out['KAND'][kn_id].update({'JMENO': kandidati[kn.attrib['PORADOVE_CISLO']]})                    
                
                kr_data.append(out)

        with Pool(150) as p:
            p.map(write, kr_data)
