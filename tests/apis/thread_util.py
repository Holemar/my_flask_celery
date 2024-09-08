#!python
# -*- coding:utf-8 -*-
"""
线程池工具类

ThreadPool 使用方式：
1. 创建线程池对象：pool = ThreadPool(size)  # size为线程池大小,int类型
2. 添加任务：pool.add_task(func, *args, **kwargs)  # func为任务函数, args为任务函数参数, kwargs为任务函数关键字参数
3. 等待任务执行完毕：pool.wait_completion(timeout)  # timeout为最长等待时间,int类型,单位秒,默认30秒
4. 停掉所有线程：pool.stop()  # 让程序可以正常退出

ThreadLock 使用方式：
with ThreadLock():
    # 线程安全的代码

线程锁的作用是，保证同一时刻只有一个线程在执行某段代码，防止多线程同时操作同一资源造成数据混乱。
"""

import os
import time
import logging
import threading
from queue import Queue


__all__ = ('ThreadPool', 'ThreadLock')

# 每次执行的线程数
THREAD_LINE = int(os.getenv('WEB_THREAD_LINE', 3))
G_MUTEX = threading.Lock()  # 线程锁


class MyThread(threading.Thread):
    """
    线程模型
    """
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.stop_flag = False
        self.queue = queue
        self.start()  # 因为作为一个工具，线程必须永远“在线”，所以不如让它在创建完成后直接运行，省得我们手动再去start它

    def run(self):
        while True:
            try:
                if self.stop_flag:
                    break
                if self.queue.empty():
                    time.sleep(0.1)  # 空闲时休眠一会
                    continue
                func, args, kwargs = self.queue.get()
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    logging.exception('thread execute error: %s', str(e))
                    raise ('bad execution: %s' % str(e))
                self.queue.task_done()
            except Exception as e:
                logging.exception('thread get error: %s', str(e))
                # break

    def stop(self):
        """停掉线程"""
        self.stop_flag = True


class SingletonThreadPool(type):
    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance') or cls._instance.destroy:
            cls._instance = super(SingletonThreadPool, cls).__call__(*args, **kwargs)
            return cls._instance
        else:
            size = args[0] if args else kwargs.get('size', THREAD_LINE)
            if size > cls._instance.size:
                cls._instance._add_thread(size - cls._instance.size)
                cls._instance.size = size
            return cls._instance


class ThreadPool(object, metaclass=SingletonThreadPool):
    """线程池
    使用单例模式，减少线程的开销。多次调用时，线程池的size以最大的为准。
    """
    size = THREAD_LINE
    queue = Queue()
    pool = []
    destroy = False  # 销毁标志，用于在程序退出时，让线程池自动销毁

    def __init__(self, size=THREAD_LINE):
        size = ThreadPool.size = max(size, ThreadPool.size)
        if size <= 0:
            raise ValueError('size must be greater than 0')
        elif size >= 2:
            logging.info('线程池启动线程数: %s', size)
            self._add_thread(size)

    @classmethod
    def _add_thread(cls, number):
        """添加任务"""
        for _ in range(number):
            cls.pool.append(MyThread(cls.queue))

    @classmethod
    def add_task(cls, func, *args, **kwargs):
        """添加任务"""
        if cls.size >= 2:
            cls.queue.put((func, args, kwargs))
        # 只有一个线程时，直接执行
        else:
            try:
                func(*args, **kwargs)
            except Exception as e:
                logging.exception('thread execute error: %s', str(e))

    @classmethod
    def wait_completion(cls, timeout=30):
        """等待任务全部执行完毕
        :param timeout: 最长等待时间，单位秒
        :return: 成功返回 True，失败返回 False
        """
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                # 任务全部取完，以及执行完毕
                if cls.queue.empty() and cls.queue.unfinished_tasks <= 0:
                    return True
                time.sleep(0.1)  # 空闲时休眠一会
            except Exception as e:
                logging.exception('thread wait empty error: %s', str(e))
                return False

    @classmethod
    def stop(cls):
        """停掉所有线程(让程序可以正常退出)"""
        for thd in cls.pool:
            thd.stop()
        for thd in cls.pool:
            if thd.is_alive():
                thd.join()
        cls.destroy = True
        cls.pool.clear()
        cls.size = 0


class ThreadLock(object):
    def __enter__(self):
        G_MUTEX.acquire()  # 启动线程锁
        return G_MUTEX  # 这个返回值，会传给as后面的变量

    def __exit__(self, error_type, value, trace):
        G_MUTEX.release()  # 释放线程锁
        return False  # 若返回 False, 则会 re-raise 异常。返回 True 则什么都不做。


if __name__ == '__main__':
    pool = ThreadPool(5)
    print(len(pool.pool))
    assert len(pool.pool) == 5
    pool2 = ThreadPool(10)
    print(id(pool), id(pool2))
    assert id(pool) == id(pool2)
    print(len(pool.pool), len(pool2.pool))
    assert len(pool.pool) == len(pool2.pool) == 10
    pool.stop()
    print(len(pool.pool))
    assert len(pool.pool) == 0

    # 前面的已经销毁，这里重新创建
    pool3 = ThreadPool(6)
    print(len(pool.pool), len(pool3.pool))
    assert len(pool.pool) == len(pool3.pool) == 6
    pool3.stop()
