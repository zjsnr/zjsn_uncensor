MITM_SERVER_PORT = 14514
STATIC_URL_PREFIX = f'http://static.gwy15.com/moefantasy.com/data/'
MANIFEST_URL = 'http://static.gwy15.com/moefantasy.com/warshipgirlsr.manifest.gz'

UPLOAD = [
    {
        'bin': 'rclone',
        'cmd': 'copy',
        'dest': 'gdrive:zjsn/'
    }
]
