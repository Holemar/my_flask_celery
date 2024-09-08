# -*- coding:utf-8 -*-


from __init__ import get, post, set_host  # 导入环境


def get_status():
    uri = 'status'
    get(uri, param={
        # 'url': 1,
        # 'models': 1,
        # 'config': 1,
        'beat': 1,
    }, return_json=True)


if __name__ == '__main__':
    # set_host('http://localhost:8000/')
    set_host('http://54.219.179.117:8134/')  # 线上环境

    get_status()
