import gzip as compressLib
import json
import hashlib
import asyncio
from pathlib import Path

import requests
import aiohttp
import async_pool
import progressbar

__VERSION__ = '4.4.0'
__CHANNEL__ = 100014
__MARKET__ = 2


class ListDiffer():
    def __init__(self, origin, new):
        originDict = self.list2Dict(origin)
        newDict = self.list2Dict(new)

        self.same = []
        self.diff = []
        self.deleted = []
        self.new = []
        for k in originDict:
            v1 = originDict[k]
            if k in newDict:
                if originDict[k] == newDict[k]:
                    self.same.append((k, v1, newDict[k]))
                else:
                    self.diff.append((k, v1, newDict[k]))
            else:
                self.deleted.append((k, v1, None))
        for k in newDict:
            if k not in originDict:
                self.new.append((k, None, newDict[k]))

    @staticmethod
    def list2Dict(arr):
        return {
            item['name']: (item['size'], item['md5'])
            for item in arr
        }


class ResourceDownloader():
    @staticmethod
    def getManifestUrls():
        version_url = f'http://version.jr.moefantasy.com/index/checkVer/{__VERSION__}/{__CHANNEL__}/{__MARKET__}'
        version_url += f'&version={__VERSION__}&channel={__CHANNEL__}&market={__MARKET__}'

        versionData = requests.get(version_url).json()
        resourceVersion = versionData['DataVersion']  # resource version
        uncensoredManifestUrl = versionData['ResUrlWu']
        # [:versionData['ResUrlWu'].find('?')] # remove query string
        manifestUrl = versionData['ResUrl']
        return {
            'censored': manifestUrl,
            'uncensored': uncensoredManifestUrl
        }

    @staticmethod
    def getManifestData(manifestUrl):
        resp = requests.get(manifestUrl)
        if resp.status_code != 200:
            print(manifestUrl)
            raise RuntimeError(resp.text)
        manifestContentCompressed = resp.content
        manifestContent = compressLib.decompress(manifestContentCompressed)
        manifestData = json.loads(manifestContent.decode())
        return manifestData

    def run(self):
        manifestUrls = self.getManifestUrls()

        censoredManifestData = self.getManifestData(manifestUrls['censored'])
        self.censoredVersion = censoredManifestData['version']

        uncensoredManifestData = self.getManifestData(
            manifestUrls['uncensored'])
        self.uncensoredVersion = uncensoredManifestData['version']

        # compare
        differ = ListDiffer(
            censoredManifestData['hot'], uncensoredManifestData['hot'])
        print('same', len(differ.same))
        print('diff', len(differ.diff))
        print('new', len(differ.new))
        print('deleted', len(differ.deleted))

        # download new and diff
        targets = differ.diff + differ.new
        urlPrefix = uncensoredManifestData['packageUrl']
        targets = [
            (urlPrefix, name, *uncensored)
            for name, censored, uncensored in targets
        ]

        bar = progressbar.ProgressBar(max_value=len(targets))

        async def f(args):
            await self.downloadUrl(*args)
            bar.update(bar.value + 1)

        bar.start()
        with async_pool.Pool(10) as pool:
            pool.map(f, targets)
        bar.finish()

    async def downloadUrl(self, prefix, name, size, md5, downloadPath='data'):
        path = Path(downloadPath)
        path.mkdir(exist_ok=True)
        *pathNames, filename = name.split('/')
        for d in pathNames:
            path = path / d
            path.mkdir(exist_ok=True)
        filePath = path / filename

        if filePath.exists() and filePath.stat().st_size == size:
            with filePath.open('rb') as f:
                if hashlib.md5(f.read()).hexdigest() == md5:
                    return

        url = prefix + name + '?md5=' + md5
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as resp:
                data = await resp.read()
        with filePath.open('wb') as f:
            f.write(data)


if __name__ == "__main__":
    ResourceDownloader().run()
