import json
import gzip
from zjsn_uncensor import config

def main():
    with open('./uncensoredManifest.json', 'rb') as f:
        data = json.load(f)
    data['packageUrl'] = config.STATIC_URL_PREFIX

    with gzip.GzipFile('data/warshipgirlsr.manifest.gz', 'wb') as f:
        f.write(json.dumps(data).encode())
