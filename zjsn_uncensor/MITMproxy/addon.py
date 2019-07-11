'''
实现 MITM 的主体插件
'''
from zjsn_uncensor import config
from mitmproxy import http
import os
import re
import gzip
import zlib
import json
import logging
import time
import requests

logger = logging.getLogger('Zjsn.Uncensor.MITM')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


def catch(func):
    def newfunc(*args, **kws):
        try:
            return func(*args, **kws)
        except Exception as ex:
            import traceback
            traceback.print_exc()
            raise
    return newfunc


def cache_for(seconds):
    def wrapper(function):
        def newfunction(*args, **kws):
            cache = getattr(cache_for, '__cache__', None)
            if cache is not None:
                result, t = cache
                if time.time() < t + seconds:
                    return result
            result = function(*args, **kws)
            cache_for.__cache__ = (result, time.time())
            return result
        return newfunction
    return wrapper


@cache_for(600)
def isResource403(manifestUrl):
    r = requests.get(manifestUrl)
    if r.status_code == 403:
        return True
    elif r.status_code == 200:
        return False
    raise RuntimeError(f'Unknown status code {r} for {manifestUrl}.')


class ZjsnHelper:
    # @catch
    def http_connect(self, flow: http.HTTPFlow):
        pass

    # @catch
    def request(self, flow: http.HTTPFlow):
        logger.debug(f'requesting url {flow.request.url}')
        # filter domains
        valid = any(
            domain in flow.request.host for domain in config.MITM_ALLOWED_DOMAINS)
        if not valid:
            logger.debug('Unvalid domain')
            flow.response = http.HTTPResponse.make(403, b'')

    # @catch
    def response(self, flow: http.HTTPFlow):
        logger.debug(f'response host {flow.request.host}')

        if '/test' in flow.request.url:
            self.onTest(flow)
            return

        if '/index/checkVer' in flow.request.url:
            self.onVersionCheck(flow)
            return

    def onTest(self, flow: http.HTTPFlow):
        flow.response.set_text(
            r'<html><h1>代理正常工作</h1></html>')

    def onVersionCheck(self, flow: http.HTTPFlow):
        '替换 version check'
        logger.debug('replacing version check...')
        data = json.loads(flow.response.get_text())

        data['ResUrlWu'] = data['ResUrlWu'].replace('/censor/', '/2/')
        is403 = isResource403(data['ResUrlWu'])
        if is403:
            print('Resource 403. Replace with self CDN.')
            data['ResUrl'] = config.MANIFEST_URL
            data['ResUrlWu'] = config.MANIFEST_URL
        else:
            print('Resource ok. Use official CDN.')
            data['ResUrl'] = data['ResUrlWu']
        data['cheatsCheck'] = 1

        flow.response.set_text(json.dumps(data))

        logger.info('Version check data replaced.')


zjsnHelper = ZjsnHelper()


def request(flow):
    return zjsnHelper.request(flow)


def http_connect(flow):
    return zjsnHelper.http_connect(flow)


def response(flow):
    return zjsnHelper.response(flow)
