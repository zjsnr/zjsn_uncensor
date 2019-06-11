import requests

r = requests.get(
    'http://version.jr.moefantasy.com/index/checkVer/4.4.0/100014/2&version=4.4.0&channel=100014&market=2',
    proxies = {
        'http':'http://do.gwy15.com:14514'
    }
)
print(r.json())

