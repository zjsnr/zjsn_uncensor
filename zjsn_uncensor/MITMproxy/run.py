import os
import sys
import re
import json
import gzip


from mitmproxy.master import Master
from mitmproxy.proxy import ProxyConfig, ProxyServer
from mitmproxy.addons import core
from mitmproxy.options import Options

from zjsn_uncensor.MITMproxy.addon import ZjsnHelper
from zjsn_uncensor import config

class TestInterceptor(Master):
    def __init__(self, options, server):
        Master.__init__(self, options)
        self.addons.add(core.Core())
        self.addons.add(ZjsnHelper())
        self.server = server

    def run(self):
        while True:
            try:
                Master.run(self)
            except KeyboardInterrupt:
                self.shutdown()
                sys.exit(0)


def start_proxy(port):
    options = Options(
        listen_port=port,
    )
    # options.body_size_limit='3m'
    config = ProxyConfig(
        options=options,
        #    cacert = os.path.expanduser('./mitmproxy.pem'),
    )
    server = ProxyServer(config)
    print('Intercepting Proxy listening on {0}'.format(port))
    m = TestInterceptor(options, server)
    m.run()


def main():
    start_proxy(config.MITM_SERVER_PORT)


if __name__ == '__main__':
    main()
