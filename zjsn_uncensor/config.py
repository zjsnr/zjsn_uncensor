from zjsn_uncensor import ip

# MITM
MITM_SERVER_PORT = 14514
MITM_ALLOWED_DOMAINS = ('moefantasy.com', 'gwy15.com', 'localhost')

# static server
STATIC_SERVER_PORT = 8080
STATIC_URL_PREFIX = 'http://{ip}:{port}/moefantasy.com/data/'.format(
    ip=ip.getIP(), port=STATIC_SERVER_PORT)
MANIFEST_URL = 'http://{ip}:{port}/moefantasy.com/warshipgirlsr.manifest.gz'.format(
    ip=ip.getIP(), port=STATIC_SERVER_PORT)
