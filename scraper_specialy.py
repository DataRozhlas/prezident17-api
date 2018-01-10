
# coding: utf-8

# In[3]:


import requests
import json
import xml.etree.ElementTree as ET
from time import gmtime, strftime, sleep
import time
import datetime
import boto3
from var import *
from ob_kat import velikosti

# In[4]:


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


# In[6]:


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


# In[7]:


ns = '{http://www.volby.cz/prezident/}'
s3 = boto3.client('s3')


# In[8]:


while True:
    data = []
    for kraj in kraje:
        print(kraje[kraj])
        kr_data = []
        now = str(datetime.datetime.utcnow().isoformat()) + 'Z'
        r = requests.get(endpoint + '/vysledky_kraj?kolo=' + kolo + '&nuts=' + kraj)
        root = ET.fromstring(r.text)
        for okres in root[0].findall(ns + 'OKRES'):    
            for obec in okres.findall(ns + 'OBEC'):
                if obec.attrib['TYP_OBEC'] == 'MCMO': #pokud ma obec mestske casti, tak vyhodit
                    continue
                out = {
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
                
                data.append(out)
    # dopocitani procent v obci
    for obec in data:
        for kand in obec['KAND']:
            obec['KAND'][kand]['PCT'] = (int(obec['KAND'][kand]['HLASY']) / int(obec['PLATNE_HLASY'])) * 100
            
    vel_obce = {'PODIL_CR': {}}
    for v in velikosti:
        filtered = list(filter(lambda x : int(x['CIS_OBEC']) in velikosti[v], data))
        for kand in kandidati:
            if kand not in vel_obce:
                vel_obce[kand] = {'jmeno': kandidati[kand]}
            suma = 0
            k_hlasy = 0
            for obec in filtered:
                suma += int(obec['PLATNE_HLASY'])
                k_hlasy += int(obec['KAND'][kand]['HLASY'])
                
            if suma == 0:
                suma = -1
                
            vel_obce[kand].update({v: (k_hlasy / suma) * 100})
            vel_obce[kand].update({v + '_abs': k_hlasy})
            
            if suma == -1:
                suma = 0
            
            vel_obce['PODIL_CR'][v] = suma
            
    putFile = s3.put_object(Bucket='prezident17', 
                            Key='kolo' + kolo + '/vel_obce.json', 
                            Body=json.dumps(vel_obce), 
                            ACL='public-read', 
                            ContentType='application/json')
    
    # top a bottom X
    def clean(lst, kand):
        out = {}
        for obec in lst:
            out[obec['CIS_OBEC']] = {
                'NAZ_OBEC': obec['NAZ_OBEC'], 
                'NAZ_OKRES': obec['NAZ_OKRES'],
                'PLATNE_HLASY': int(obec['PLATNE_HLASY']),
                'ZAPSANI_VOLICI': int(obec['ZAPSANI_VOLICI']),
                'KAND_HLASU_PCT': obec['KAND'][kand]['PCT']
            }
        return out

    top_bottom = {}
    for kand in kandidati:
        top_bottom[kand] = {'jmeno': kandidati[kand]}
        srt = sorted(data, key=lambda x: x['KAND'][kand]['PCT'])
        top_bottom[kand]['top'] = clean(srt[-10:], kand)
        top_bottom[kand]['bottom'] = clean(srt[0:10], kand)
        
    putFile = s3.put_object(Bucket='prezident17', 
                            Key='kolo' + kolo + '/top_bottom.json',
                            Body=json.dumps(top_bottom), 
                            ACL='public-read', 
                            ContentType='application/json')
    
    # zbyva secist
    filtered = list(filter(lambda x : float(x['OKRSKY_ZPRAC_PROC']) != 100 , data)) #BACHA, zde nastavit != 100
    srt = sorted(filtered, key=lambda x: float(x['OKRSKY_ZPRAC_PROC']), reverse=True)[0:50] #nejhorsich 50
    latest = {'ZBYVA_CELKEM': len(filtered)}
    for obec in srt:
        latest[obec['CIS_OBEC']] = {
            'NAZ_OBEC': obec['NAZ_OBEC'], 
            'NAZ_OKRES': obec['NAZ_OKRES'], 
            'OKRSKY_CELKEM' : obec['OKRSKY_CELKEM'], 
            'OKRSKY_ZPRAC': obec['OKRSKY_ZPRAC'], 
            'OKRSKY_ZPRAC_PROC': obec['OKRSKY_ZPRAC_PROC'], 
            'ZAPSANI_VOLICI': obec['ZAPSANI_VOLICI']
        }
        
    putFile = s3.put_object(Bucket='prezident17', 
                            Key='kolo' + kolo + '/waiting.json', 
                            Body=json.dumps(latest), 
                            ACL='public-read', 
                            ContentType='application/json')        
    
    time.sleep(45)
