import gzip
import json
import random
import requests
from zjsn_uncensor import ip, config

r = requests.get(
    'http://version.jr.moefantasy.com/index/checkVer/4.5.0/100014/2&version=4.5.0&channel=100014&market=2',
    proxies={
        'http': f'http://float.gwy15.com:14514'
        # 'http': 'http://192.168.31.126:14514'
    }
)
print(r.json())
manifestUrl = r.json()['ResUrlWu']
r = requests.get(manifestUrl)
manifest = json.loads(gzip.decompress(r.content).decode())
print(manifest['packageUrl'])
for item in random.choices(manifest['hot'], k=20):
    url = manifest['packageUrl'] + item['name']
    print(url)
    r = requests.get(url)
    if r.status_code != 200:
        print(r)
