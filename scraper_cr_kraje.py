
# coding: utf-8

# In[1]:


import requests
import json
import xml.etree.ElementTree as ET
import boto3
import datetime
import time
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


kraj_cis = {
    'CZ010': '1',
    'CZ020': '2',
    'CZ031': '3',
    'CZ032': '4',
    'CZ041': '5',
    'CZ042': '6',
    'CZ051': '7',
    'CZ052': '8',
    'CZ053': '9',
    'CZ063': '10',
    'CZ064': '11',
    'CZ071': '12',
    'CZ072': '13',
    'CZ080': '14'
}


# In[4]:


while True:
    now = str(datetime.datetime.utcnow().isoformat()) + 'Z'
    print(now)
    r = requests.get(endpoint + '/vysledky_krajmesta')
    root = ET.fromstring(r.text)

    data = {'UPDATED': now}

    for kraj in root.findall(ns + 'KRAJ'):
        out = {}
        kraj_id = kraj_cis[kraj.attrib['NUTS_KRAJ']]
        out[kraj_id] = kraj.attrib
        out[kraj_id].update(kraj.find(ns + 'CELKEM').find(ns + 'UCAST').attrib)
        out[kraj_id].update({'KAND': {}})
        
        for kn in kraj.find(ns + 'CELKEM').findall(ns + 'HODN_KAND'):
            kn_id = kn.attrib['PORADOVE_CISLO']
            
            out[kraj_id]['KAND'][kn_id] = kn.attrib
            out[kraj_id]['KAND'][kn_id].update({'JMENO': kandidati[kn.attrib['PORADOVE_CISLO']]})
            
        data.update(out)
    
    # krajska mesta
    for kmesto in root.findall(ns + 'OBEC'):
        out = {}
        kmesto_id = kmesto.attrib['CIS_OBEC']
        out[kmesto_id] = kraj.attrib
        out[kmesto_id].update(kmesto.find(ns + 'UCAST').attrib)
        out[kmesto_id].update({'KAND': {}})
        
        for kn in kmesto.findall(ns + 'HODN_KAND'):
            kn_id = kn.attrib['PORADOVE_CISLO']
            
            out[kmesto_id]['KAND'][kn_id] = kn.attrib
            out[kmesto_id]['KAND'][kn_id].update({'JMENO': kandidati[kn.attrib['PORADOVE_CISLO']]})
            
        data.update(out)
    
        
    #celá ČR
    r = requests.get(endpoint + '/vysledky')
    root = ET.fromstring(r.text)
    
    out = {'99': root.find(ns + 'CR').findall(ns + 'UCAST')[0].attrib}
    out['99'].update({'NAZ_KRAJ': 'ČR', 'KAND': {}})
    
    for kn in root.find(ns + 'CR').findall(ns + 'KANDIDAT'):
        kn_id = kn.attrib['PORADOVE_CISLO']
            
        out['99']['KAND'][kn_id] = kn.attrib
        out['99']['KAND'][kn_id].update({'JMENO': kandidati[kn.attrib['PORADOVE_CISLO']]})
    
    data.update(out)
    
    #zahr celkem
    r = requests.get(endpoint + '/vysledky_zahranici')
    root = ET.fromstring(r.text)
    
    out = {}
    out = {'00': root[0].find(ns + 'CELKEM').find(ns + 'UCAST').attrib}
    out['00'].update({'NAZ_KRAJ': 'Zahraničí', 'KAND': {}})
        
    for kn in root[0].find(ns + 'CELKEM').findall(ns + 'HODN_KAND'):
        kn_id = kn.attrib['PORADOVE_CISLO']

        out['00']['KAND'][kn_id] = kn.attrib
        out['00']['KAND'][kn_id].update({'JMENO': kandidati[kn.attrib['PORADOVE_CISLO']]})

    data.update(out)
        
    #put data
    putFile = s3.put_object(Bucket='prezident17', 
                            Key='kolo' + kolo + '/cr_kraje.json', 
                            Body=json.dumps(data), 
                            ACL='public-read', 
                            ContentType='application/json')
    
    time.sleep(30)
