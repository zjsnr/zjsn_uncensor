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

logger = logging.getLogger('Zjsn.Uncensor.MITM')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


manifestUrl = config.MANIFEST_URL
assert 'moefantasy.com' in manifestUrl


def catch(func):
    def newfunc(*args, **kws):
        try:
            return func(*args, **kws)
        except Exception as ex:
            import traceback
            traceback.print_exc()
            raise
    return newfunc


class ZjsnHelper:
    ALLOWED_DOMAINS = ('moefantasy.com', 'gwy15.com', 'localhost')

    # @catch
    def http_connect(self, flow: http.HTTPFlow):
        pass

    # @catch
    def request(self, flow: http.HTTPFlow):
        logger.debug(f'requesting url {flow.request.url}')
        # filter domains
        valid = any(
            domain in flow.request.host for domain in self.ALLOWED_DOMAINS)
        if not valid:
            logger.debug('Unvalid domain')
            flow.response = http.HTTPResponse.make(404, b'')

    # @catch
    def response(self, flow: http.HTTPFlow):
        logger.debug(f'response host {flow.request.host}')

        if '/index/checkVer' in flow.request.url:
            self.onVersionCheck(flow)
            return

    def onVersionCheck(self, flow: http.HTTPFlow):
        '替换 version check'
        logger.debug('replacing version check...')
        data = json.loads(flow.response.get_text())

        data['ResUrl'] = manifestUrl
        data['ResUrlWu'] = manifestUrl
        logger.info('Version check data replaced.')

        flow.response.set_text(json.dumps(data))


zjsnHelper = ZjsnHelper()


def request(flow):
    return zjsnHelper.request(flow)


def http_connect(flow):
    return zjsnHelper.http_connect(flow)


def response(flow):
    return zjsnHelper.response(flow)
