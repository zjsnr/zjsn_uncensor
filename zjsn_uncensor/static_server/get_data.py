import gzip as compressLib
import json
import hashlib
import asyncio
from pathlib import Path
import dataclasses

import requests
import aiohttp
import async_pool
import progressbar

__VERSION__ = '4.4.0'
__CHANNEL__ = 100014
__MARKET__ = 2


@dataclasses.dataclass
class File:
    name: str
    size: int
    md5: str

    def __hash__(self):
        return int(self.md5, base=16)

    def toDict(self):
        return {
            'name': self.name,
            'size': self.size,
            'md5': self.md5
        }


class ListDiffer():
    def __init__(self, censored, uncensored):
        self.same = censored & uncensored
        self.censored_only = censored - uncensored
        self.uncensored_only = uncensored - censored


class ResourceDownloader():
    @staticmethod
    def getManifestUrls():
        version_url = f'http://version.jr.moefantasy.com/index/checkVer/{__VERSION__}/{__CHANNEL__}/{__MARKET__}'
        version_url += f'&version={__VERSION__}&channel={__CHANNEL__}&market={__MARKET__}'

        print(f'getting {version_url}')
        versionData = requests.get(version_url).json()
        resourceVersion = versionData['DataVersion']  # resource version

        return {
            'censored': versionData['ResUrl'],
            'uncensored': versionData['ResUrlWu']
        }

    @staticmethod
    def getManifestData(manifestUrl):
        resp = requests.get(manifestUrl)
        if resp.status_code != 200:
            print('Manifest download failed. Retring with no query string.')
            # remove query string
            manifestUrl = manifestUrl[:manifestUrl.find('?')]
            resp = requests.get(manifestUrl)
            if resp.status_code != 200:
                raise RuntimeError(resp.text)

        manifestContent = compressLib.decompress(resp.content)
        manifestData = json.loads(manifestContent.decode())
        return manifestData

    def run(self):
        manifestUrls = self.getManifestUrls()
        print(manifestUrls)

        # get file lists
        censoredManifestData = self.getManifestData(manifestUrls['censored'])
        self.censoredVersion = censoredManifestData['version']
        self.censoredPrefix = censoredManifestData['packageUrl']
        self.censoredFiles = set(File(**item)
                                 for item in censoredManifestData['hot'])
        with open('censoredManifest.json', 'w') as f:
            json.dump(censoredManifestData, f)

        uncensoredManifestData = self.getManifestData(
            manifestUrls['uncensored'])
        self.uncensoredVersion = uncensoredManifestData['version']
        self.uncensoredPrefix = uncensoredManifestData['packageUrl']
        self.uncensoredFiles = set(File(**item)
                                   for item in uncensoredManifestData['hot'])
        with open('uncensoredManifest.json', 'w') as f:
            json.dump(uncensoredManifestData, f)

        print('Censored version:', self.censoredVersion)
        print('Uncensored version:', self.uncensoredVersion)

        # compare
        differ = ListDiffer(self.censoredFiles, self.uncensoredFiles)
        print('same', len(differ.same))
        print('censored only', len(differ.censored_only))
        print('uncensored only', len(differ.uncensored_only))

        # download common
        self.downloadFiles(self.uncensoredPrefix,
                           differ.uncensored_only, 'uncensored', version=self.uncensoredVersion)
        self.downloadFiles(self.censoredPrefix,
                           differ.censored_only, 'censored', version=self.censoredVersion)
        self.downloadFiles(self.censoredPrefix, differ.same,
                           'common', version=self.censoredVersion)

    def downloadFiles(self, prefix, files, name, version, downloadPath='data'):
        print('Total size: {:.2f} MiB'.format(
            sum(f.size for f in files) / 1024 / 1024))

        path = downloadPath / name

        bar = progressbar.ProgressBar(max_value=len(files))

        async def f(file: File):
            await self.downloadUrl(prefix, file.name, file.size, file.md5, path)
            bar.update(bar.value + 1)

        bar.start()
        with async_pool.Pool(10) as pool:
            pool.map(f, files)
        bar.finish()

        with (Path(path) / f'{name}.json').open('w') as f:
            json.dump({
                'version': version,
                'files': [f.toDict() for f in files]
            }, f)

    async def downloadUrl(self, prefix, name, size, md5, downloadPath):
        # ensure parent path exists
        path = Path(downloadPath)
        path.mkdir(exist_ok=True)
        *pathNames, filename = name.split('/')
        for d in pathNames:
            path = path / d
            path.mkdir(exist_ok=True)
        filePath = path / filename

        # skip existing file
        if filePath.exists() and filePath.stat().st_size == size:
            with filePath.open('rb') as f:
                if hashlib.md5(f.read()).hexdigest() == md5:
                    return

        url = prefix + name + '?md5=' + md5
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as resp:
                if resp.status != 200:
                    raise RuntimeError(f'{url} status code: {resp.status}')
                data = await resp.read()
                if len(data) != size:
                    raise RuntimeError(
                        f'{url} size doesn\'t match. {size} bytes expected, got {len(data)} bytes.')

        with filePath.open('wb') as f:
            f.write(data)


if __name__ == "__main__":
    ResourceDownloader().run()
