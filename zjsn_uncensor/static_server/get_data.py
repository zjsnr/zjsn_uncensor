import gzip as compressLib
import json
import hashlib
import asyncio
from pathlib import Path
import dataclasses
import subprocess

import requests
import aiohttp
import async_pool
import progressbar

from zjsn_uncensor import config

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

        versionData = requests.get(version_url).json()
        if versionData.get('eid', None) == -9999:
            raise RuntimeError('WDNMD 真就维护了呗？')

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
        self.downloadPath = 'data'
        self.download()
        self.upload()

    def download(self):
        manifestUrls = self.getManifestUrls()
        print(manifestUrls)

        # get file lists
        censoredManifestData = self.getManifestData(manifestUrls['censored'])
        censoredVersion = censoredManifestData['version']
        censoredPrefix = censoredManifestData['packageUrl']
        censoredFiles = set(File(**item)
                            for item in censoredManifestData['hot'])
        del censoredManifestData # save RAM

        uncensoredManifestData = self.getManifestData(
            manifestUrls['uncensored'])
        uncensoredVersion = uncensoredManifestData['version']
        uncensoredPrefix = uncensoredManifestData['packageUrl']
        uncensoredFiles = set(File(**item)
                              for item in uncensoredManifestData['hot'])
        del uncensoredManifestData # save RAM

        print('Censored version:', censoredVersion)
        print('Uncensored version:', uncensoredVersion)

        # compare
        differ = ListDiffer(censoredFiles, uncensoredFiles)
        print('same', len(differ.same))
        print('censored only', len(differ.censored_only))
        print('uncensored only', len(differ.uncensored_only))

        # download files
        path = Path(self.downloadPath)
        self.downloadFiles(uncensoredPrefix, differ.uncensored_only,
                           'uncensored', uncensoredVersion, path)
        self.downloadFiles(censoredPrefix, differ.censored_only,
                           'censored', censoredVersion, path)
        self.downloadFiles(censoredPrefix, differ.same,
                           'common', censoredVersion, path)

    def downloadFiles(self, prefix, files, name, version, downloadRootPath: Path):
        print('{}: total size: {:.2f} MiB'.format(
            name, sum(f.size for f in files) / 1024 / 1024))

        downloadRootPath.mkdir(exist_ok=True)
        path = downloadRootPath / name

        bar = progressbar.ProgressBar(max_value=len(files))

        async def f(file: File):
            await self.downloadUrl(prefix, file, path)
            bar.update(bar.value + 1)

        bar.start()
        with async_pool.Pool(10) as pool:
            pool.map(f, files)
        bar.finish()

        with (path / f'{name}.json').open('w') as f:
            json.dump({
                'version': version,
                'files': [f.toDict() for f in files]
            }, f)

    async def downloadUrl(self, prefix, file, path: Path):
        # ensure parent path exists
        path = path
        path.mkdir(exist_ok=True)
        *pathNames, filename = file.name.split('/')
        for d in pathNames:
            path = path / d
            path.mkdir(exist_ok=True)
        filePath = path / filename

        # skip existing file
        if filePath.exists() and filePath.stat().st_size == file.size:
            with filePath.open('rb') as f:
                if hashlib.md5(f.read()).hexdigest() == file.md5:
                    return

        # build url
        url = prefix + file.name + '?md5=' + file.md5
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as resp:
                if resp.status != 200:
                    raise RuntimeError(f'{url} status code: {resp.status}')
                data = await resp.read()
                if len(data) != file.size:
                    raise RuntimeError(
                        f'{url} size doesn\'t match. {file.size} bytes expected, got {len(data)} bytes.')

        with filePath.open('wb') as f:
            f.write(data)

    def upload(self):
        for item in config.UPLOAD:
            args = [
                item['bin'], item['cmd'], self.downloadPath, item['dest']
            ]
            with subprocess.Popen(args, stdout=subprocess.PIPE) as proc:
                print(proc.stdout.read())


if __name__ == "__main__":
    ResourceDownloader().run()
