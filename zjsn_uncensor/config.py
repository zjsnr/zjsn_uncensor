MITM_SERVER_PORT = 14514
STATIC_SERVER_PORT = 14515
STATIC_URL_PREFIX = f'http://192.168.137.1:{STATIC_SERVER_PORT}/zjsn/'

UPLOAD = [
    {
        'bin': 'rclone',
        'cmd': 'copy',
        'dest': 'gdrive:zjsn/'
    }
]
