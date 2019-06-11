'''
实现 MITM 的主体插件
'''
import os
import re
import gzip
import zlib
import json

from mitmproxy import http
from zjsn_uncensor import config

manifestUrl = config.STATIC_URL_PREFIX + 'warshipgirlsr.manifest.gz'


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
    VERSION_HOST = re.compile(r'version(\.channel)?\.jr\.moefantasy\.com')

    @catch
    def http_connect(self, flow):
        pass

    @catch
    def request(self, flow: http.HTTPFlow):
        if 'jr.moefantasy.com' not in flow.request.host:
            flow.response = http.HTTPResponse.make(404, b'')

    @catch
    def response(self, flow: http.HTTPFlow):
        print(f'response host: {flow.request.host}')
        if re.match(self.VERSION_HOST, flow.request.host):
            self.onVersionCheck(flow)

    def onVersionCheck(self, flow: http.HTTPFlow):
        '替换 version check'
        print('replacing version check...')
        data = json.loads(flow.response.get_text())

        data['ResUrl'] = manifestUrl
        data['ResUrlWu'] = manifestUrl

        flow.response.set_text(json.dumps(data))


def request(flow):
    return ZjsnHelper().request(flow)


def http_connect(flow):
    return ZjsnHelper().http_connect(flow)


def response(flow):
    return ZjsnHelper().response(flow)
