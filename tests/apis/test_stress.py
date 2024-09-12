#!python
# -*- coding:utf-8 -*-
"""
压力测试，可测试随意地址，不涉及具体某个系统，
"""
import time
import logging

from __init__ import get, post, set_host  # 导入环境
from adam.utils.thread_util import ThreadPool

THREAD_LINE = 20  # 线程数
repeat_number = 500  # 重复次数
error_time = 0  # 出错次数


# 持续地发请求(单线程)
def test_single(*args, **kwargs):
    """
    单次请求
    """
    global error_time
    start_time = time.time()
    try:
        resp_dict = get('status', param={}, return_json=True)
        assert "beat" in resp_dict
        assert "workers" in resp_dict
        assert "pend_message" in resp_dict
        assert "version" in resp_dict
        assert 0 < resp_dict.get("duration") < 1  # 响应时间在0s~1s之间
    except Exception as e:
        logging.exception(u'请求出错:%s' % e)
        error_time += 1
    # 记录总运行时间
    run_time = time.time() - start_time
    logging.info(u'test_single 耗时:%.4f 秒, 出错次数:%s', run_time, error_time)


# 持续地发请求(单线程)
def test_single2(*args, **kwargs):
    """
    单次请求
    """
    global error_time
    start_time = time.time()
    try:
        resp_dict = get('test', param={}, return_json=True)
        assert resp_dict == {"code": 0, "message": "success"}
    except Exception as e:
        logging.error(u'请求出错:%s' % e)
        error_time += 1
    # 记录总运行时间
    run_time = time.time() - start_time
    logging.info(u'test_single 耗时:%.4f 秒, 出错次数:%s', run_time, error_time)


def all_test():
    """
    并发请求测试
    """
    logging.info('请求 线程数: %s, 重复次数: %s', THREAD_LINE, repeat_number)
    start_time = time.time()
    pool = ThreadPool(THREAD_LINE)

    for i in range(repeat_number):
        pool.add_task(test_single)

    pool.wait_completion(100)
    # 记录总运行时间
    run_time = time.time() - start_time
    logging.info(u'all_test 总耗时:%.4f 秒, 出错次数:%s', run_time, error_time)


if __name__ == "__main__":
    # set_host('http://localhost:8000/')
    set_host('http://54.151.30.253:8134/')  # 线上环境

    all_test()
    ThreadPool.stop()

