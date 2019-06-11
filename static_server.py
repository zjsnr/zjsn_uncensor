import os
import flask
from flask import request
import requests
import config

app = flask.Flask(__name__)


@app.route('/<path:path>')
def proxy(path):
    filename = 'data/' + path
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            return flask.make_response(f.read())

    md5 = request.args.get('md5', 'md5')
    path += '?md5=' + md5
    print(f'getting {path}')
    url = 'http://bshot.moefantasy.com/censor/' + path
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f'path {path} fallback for 2 (status code {resp.status_code})')
        url = 'http://bshot.moefantasy.com/2/' + path
        resp = requests.get(url)
        if resp.status_code != 200:
            print(
                f'both censor and 2 failed (2 with status code {resp.status_code}).')
            print(f'failed url: {url}')
            flask.abort(404)
    print(f'{url} success')
    return flask.make_response(resp.content)


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=config.STATIC_SERVER_PORT)
