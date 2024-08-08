#!python
# -*- coding:utf-8 -*-
"""
公用函数 time_util.py 的测试
Created on 2014/10/16
Updated on 2022/02/21
@author: Holemar
"""
import time
from datetime import datetime, date, timedelta, time as dt
import unittest

from adam.time_util import *

now = lambda: datetime.now().replace(microsecond=0)


def _sub_dict(**kwargs):
    zero_secends = {'years': 0, 'months': 0, 'days': 0, 'hours': 0, 'minutes': 0, 'seconds': 0, 'sum_days': 0,
                    'sum_seconds': 0}
    zero_secends.update(kwargs)
    return zero_secends


class TimeUtilTest(unittest.TestCase):

    def test_to_string(self):
        now_str = lambda: now().strftime('%Y-%m-%d %H:%M:%S')
        # default and now value test
        self.assertEqual(to_string(), None)
        self.assertEqual(to_string(default_now=True), now_str())  # default now
        self.assertEqual(to_string(None), None)
        self.assertEqual(to_string(None, default_now=True), now_str())  # default now
        self.assertEqual(to_string(''), None)
        self.assertEqual(to_string('', default_now=True), now_str())  # default now
        self.assertEqual(to_string(time.time()), now_str())  # timestamp
        self.assertEqual(to_string(0), to_string(time.localtime(0)))  # timestamp is 0
        # timedelta
        self.assertEqual(to_string(timedelta()), to_string(0))
        self.assertEqual(to_string(timedelta(0, 3602)), to_string(3602))
        self.assertEqual(to_string(timedelta(5, 3602)), to_string(5 * 24 * 3600 + 3602))
        # more formats test
        self.assertEqual(to_string('2014-02-06 08:51:06'), '2014-02-06 08:51:06')
        self.assertEqual(to_string('2014-2-6 8:51:06'), '2014-02-06 08:51:06')
        self.assertEqual(to_string('2014/02/06'), '2014-02-06 00:00:00')
        self.assertEqual(to_string('2014/2/6 23:59:59'), '2014-02-06 23:59:59')
        self.assertEqual(to_string('2014/2/6 23:59'), '2014-02-06 23:59:00')
        self.assertEqual(to_string('2014-2-06 23:59'), '2014-02-06 23:59:00')
        self.assertEqual(to_string('2014年2月6日 23:59'), '2014-02-06 23:59:00')
        self.assertEqual(to_string('2014年2月6日 23时59分'), '2014-02-06 23:59:00')
        self.assertEqual(to_string('2014年02月6日 23时59分0秒'), '2014-02-06 23:59:00')
        self.assertEqual(to_string('2014年2月06日 23:59:00'), '2014-02-06 23:59:00')
        self.assertEqual(to_string('2014-2-6T23:59'), '2014-02-06 23:59:00')
        self.assertEqual(to_string('2014-2-6T23:59:00'), '2014-02-06 23:59:00')
        self.assertEqual(to_string('1900-1-1'), '1900-01-01 00:00:00')
        self.assertEqual(to_string('197011'), '1970-01-01 00:00:00')
        self.assertEqual(to_string('197011810'), '1970-01-01 08:01:00')
        self.assertEqual(to_string('2014-2-6 下午 11:59:00'), '2014-02-06 23:59:00')
        self.assertEqual(to_string('2014-2-6 下午 11:59'), '2014-02-06 23:59:00')
        self.assertEqual(to_string('2014-2-6 PM 11:59:00'), '2014-02-06 23:59:00')
        self.assertEqual(to_string('2014-2-6 PM 11:59'), '2014-02-06 23:59:00')
        self.assertEqual(to_string('2014/02/06 下午 11:59'), '2014-02-06 23:59:00')
        self.assertEqual(to_string('2014/02/06 PM 11:59:00'), '2014-02-06 23:59:00')
        self.assertEqual(to_string('2014-02/06 08:51:06'), '2014-02-06 08:51:06')  # the wrong format str

        # datetime, time, date, datetime.time type test
        test_time = datetime(2014, 2, 6, 8, 51, 6)
        self.assertEqual(to_string(test_time), '2014-02-06 08:51:06')
        self.assertEqual(to_string(time.strptime('2014/03/25 19:05:33', '%Y/%m/%d %H:%M:%S')), '2014-03-25 19:05:33')
        self.assertEqual(to_string(date.today()), now().strftime('%Y-%m-%d'))
        self.assertEqual(to_string(dt(12, 9, 2)), "12:09:02")
        # set format
        self.assertEqual(to_string(test_time, '%Y/%m/%dxx'), '2014/02/06xx')
        self.assertEqual(to_string(test_time, '%Y-%m/%dxx%H+%M+%S'), '2014-02/06xx08+51+06')
        self.assertEqual(to_string('2014-02-06 08:51:06', '%Y/%m/%d %H:%Mxx'), '2014/02/06 08:51xx')

    def fun_test(self, fun, default_time, test_time, test_date):
        # default and now value test
        self.assertEqual(fun(), None)
        self.assertEqual(fun(default_now=True), default_time())  # default now
        self.assertEqual(fun(None), None)
        self.assertEqual(fun(None, default_now=True), default_time())  # default now
        self.assertEqual(fun(''), None)
        self.assertEqual(fun('', default_now=True), default_time())  # default now
        self.assertEqual(fun(time.time()), default_time())  # timestamp
        self.assertEqual(fun(0), fun(time.localtime(0)))  # timestamp is 0
        self.assertEqual(fun(0, default_now=True), fun(time.localtime(0)))  # timestamp is 0
        # datetime, time, date, str type test
        self.assertEqual(fun('2014-02-06 08:51:06'), test_time)
        self.assertEqual(fun('2014/02-6 8xx51mm06::YY', from_format='%Y/%m-%d %Hxx%Mmm%S::YY'), test_time)  # format
        self.assertEqual(fun(datetime(2014, 2, 6, 8, 51, 6)), test_time)  # datetime
        self.assertEqual(fun(time.strptime('2014-02-06 08:51:06', '%Y-%m-%d %H:%M:%S')), test_time)  # time
        self.assertEqual(fun(date(2014, 2, 6)), test_date)  # date
        # more formats test
        self.assertEqual(fun('2014/02/06 08:51:06'), test_time)
        self.assertEqual(fun('20142685106'), test_time)
        self.assertEqual(fun('2014268516'), test_time)
        self.assertEqual(fun('2014/2/6 8:51:6'), test_time)
        self.assertEqual(fun('2014/2/06 08:51:6'), test_time)
        self.assertEqual(fun('2014-02-06T08:51:06'), test_time)
        self.assertEqual(fun('2014-02-06T08:51:06+08:00'), test_time)
        self.assertEqual(fun('2014-02-06T08:51:06.000Z'), test_time)
        self.assertEqual(fun('2014-02-06 AM 08:51:06'), test_time)
        self.assertEqual(fun('2014-02-06 上午 08:51:06'), test_time)
        self.assertEqual(fun(u'2014-02-06 上午 08:51:06'), test_time)
        self.assertEqual(fun('2014/2/06 AM 08:51:06'), test_time)
        self.assertEqual(fun('2014/02/06 上午 08:51:06'), test_time)
        # date test
        self.assertEqual(fun('2014-02-06'), test_date)
        self.assertEqual(fun('2014-2-6'), test_date)
        self.assertEqual(fun('2014/02/06'), test_date)
        self.assertEqual(fun('2014/2/6'), test_date)
        self.assertEqual(fun('201426'), test_date)
        # timedelta type
        if fun == to_time:
            self.assertEqual(fun(timedelta())[:6], fun(0)[:6])
            self.assertEqual(fun(timedelta(0, 3602))[:6], fun(3602)[:6])
            self.assertEqual(fun(timedelta(5, 3602))[:6], fun(5 * 24 * 3600 + 3602)[:6])
        else:
            self.assertEqual(fun(timedelta()), fun(0))
            self.assertEqual(fun(timedelta(0, 3602)), fun(3602))
            self.assertEqual(fun(timedelta(5, 3602)), fun(5 * 24 * 3600 + 3602))

    def test_to_time(self):
        now_time = time.localtime
        test_time = time.strptime('2014-02-06 08:51:06', '%Y-%m-%d %H:%M:%S')  # datetime
        test_date = time.strptime('2014-02-06', '%Y-%m-%d')  # date
        self.fun_test(to_time, now_time, test_time, test_date)

    def my_to_datetime(self, *args, **kwargs):
        res = to_datetime(*args, **kwargs)
        res = res.replace(microsecond=0) if res else res  # ignore microsecond
        return res

    def test_to_datetime(self):
        test_time = datetime(2014, 2, 6, 8, 51, 6)  # datetime
        test_date = datetime(2014, 2, 6)  # date
        self.fun_test(self.my_to_datetime, now, test_time, test_date)

    def test_to_date(self):
        now_time = date.today
        test_time = date(2014, 2, 6)  # datetime
        test_date = date(2014, 2, 6)  # date
        self.fun_test(to_date, now_time, test_time, test_date)

    def my_to_timestamp(self, *args, **kwargs):
        res = to_timestamp(*args, **kwargs)
        res = int(res) if res else res  # ignore microsecond
        return res

    def test_to_timestamp(self):
        now_time = lambda: int(time.time())
        test_time = time.mktime(time.strptime('2014-02-06 08:51:06', '%Y-%m-%d %H:%M:%S'))  # datetime
        test_date = time.mktime(time.strptime('2014-02-06', '%Y-%m-%d'))  # date
        self.fun_test(self.my_to_timestamp, now_time, test_time, test_date)

    def test_to_datetime_time(self):
        test_time = dt(12, 9, 2)
        self.assertEqual(to_datetime_time("12:9:2"), test_time)
        self.assertEqual(to_datetime_time("12:09:02"), test_time)
        self.assertEqual(to_datetime_time(test_time), test_time)
        self.assertEqual(to_datetime_time('0:0:0'), dt())
        self.assertEqual(to_datetime_time(datetime(2017, 9, 5, 15, 53, 2)), dt(15, 53, 2))
        # not second
        test_time2 = dt(12, 9)
        self.assertEqual(to_datetime_time("12:9"), test_time2)
        self.assertEqual(to_datetime_time("12:09:00"), test_time2)
        self.assertEqual(to_datetime_time("12:9:0"), test_time2)
        self.assertEqual(to_datetime_time('0:0'), dt())
        # wrong type
        self.assertEqual(to_datetime_time(None), None)
        self.assertEqual(to_datetime_time(''), None)
        self.assertEqual(to_datetime_time(12345), None)
        # self.assertEqual(to_datetime_time("2014-02-06 12:09:00"), None)
        # datetime str
        self.assertEqual(to_datetime_time('2014-02-06 08:51:06'), dt(8, 51, 6))
        self.assertEqual(to_datetime_time('2014/02/06'), dt(0, 0, 0))
        self.assertEqual(to_datetime_time('2014/2/6 23:59:59'), dt(23, 59, 59))
        self.assertEqual(to_datetime_time('2014/2/6 23:59'), dt(23, 59, 0))
        self.assertEqual(to_datetime_time('2014-2-06 23:59'), dt(23, 59, 0))
        self.assertEqual(to_datetime_time('2014年2月6日 23:59'), dt(23, 59, 0))
        self.assertEqual(to_datetime_time('2014年2月6日 23时59分'), dt(23, 59, 0))
        self.assertEqual(to_datetime_time('2014年02月6日 23时59分0秒'), dt(23, 59, 0))
        self.assertEqual(to_datetime_time('2014年2月06日 23:59:00'), dt(23, 59, 0))
        self.assertEqual(to_datetime_time('1900-1-1'), dt(0, 0, 0))
        self.assertEqual(to_datetime_time('197011'), dt(0, 0, 0))
        self.assertEqual(to_datetime_time('197011810'), dt(8, 1, 0))
        # timedelta type
        self.assertEqual(to_datetime_time(timedelta()), dt(0, 0, 0))
        self.assertEqual(to_datetime_time(timedelta(0, 3602)), dt(1, 0, 2))
        self.assertEqual(to_datetime_time(timedelta(5, 3602)), dt(1, 0, 2))

    def test_datetime_time_to_str(self):
        test_time = dt(12, 9, 2)
        self.assertEqual(datetime_time_to_str(test_time), "12:09:02")
        self.assertEqual(datetime_time_to_str(test_time, '%H:%M'), "12:09")
        self.assertEqual(datetime_time_to_str("12:9"), "12:09:00")
        self.assertEqual(datetime_time_to_str("12:9:2"), "12:09:02")
        self.assertEqual(datetime_time_to_str(dt()), "00:00:00")
        self.assertEqual(datetime_time_to_str('0:0:0'), "00:00:00")
        self.assertEqual(datetime_time_to_str('0:0'), "00:00:00")
        # wrong type
        self.assertEqual(datetime_time_to_str(None), None)
        self.assertEqual(datetime_time_to_str(''), None)
        self.assertEqual(datetime_time_to_str(12345), None)
        self.assertEqual(datetime_time_to_str("2014-02-06 12:09:00"), "12:09:00")
        # timedelta type
        self.assertEqual(datetime_time_to_str(timedelta()), "00:00:00")
        self.assertEqual(datetime_time_to_str(timedelta(0, 3602)), "01:00:02")
        self.assertEqual(datetime_time_to_str(timedelta(5, 3602)), "01:00:02")
        self.assertEqual(datetime_time_to_str(timedelta(0, -2)), "23:59:58")

    # add 测试
    def test_add(self):
        test_time = datetime(2014, 10, 16)  # 测试时间
        self.assertEqual(add(), None)
        self.assertEqual(add(now(), days=11).replace(microsecond=0), now() + timedelta(days=11))
        self.assertEqual(add(now(), days=11, number=2).replace(microsecond=0), now() + timedelta(days=22))
        self.assertEqual(add(test_time), test_time)
        # 参数是否被修改测试
        tem_time = test_time
        self.assertTrue(id(add(tem_time, days=1)) != id(test_time))  # 日期不同,不能修改传进去的参数值
        self.assertTrue(id(add(tem_time, months=1)) != id(test_time))  # 日期不同,不能修改传进去的参数值
        self.assertEqual(id(tem_time), id(test_time))  # 传进去的参数不能被修改

        # add(years=1, months=0, days=0, hours=0, minutes=0, seconds=0)
        self.assertEqual(add(test_time, years=1), datetime(2015, 10, 16))  # 加 1 年
        self.assertEqual(add(test_time, years=-1), datetime(2013, 10, 16))  # 减 1 年
        self.assertEqual(add(test_time, months=1), datetime(2014, 11, 16))  # 加 1 月
        self.assertEqual(add(test_time, months=-1), datetime(2014, 9, 16))  # 减 1 月
        self.assertEqual(add(test_time, months=12), add(test_time, years=1))  # 加 12 月
        self.assertEqual(add(datetime(2014, 9, 30), days=1), datetime(2014, 10, 1))  # 加 1 天
        self.assertEqual(add(datetime(2014, 10, 1), days=-1), datetime(2014, 9, 30))  # 减 1 天
        self.assertEqual(add(datetime(2014, 10, 31), days=1), datetime(2014, 11, 1))  # 加 1 天
        self.assertEqual(add(datetime(2014, 2, 28), days=1), datetime(2014, 3, 1))  # 加 1 天
        self.assertEqual(add(datetime(2000, 2, 28), days=1), datetime(2000, 2, 29))  # 加 1 天
        self.assertEqual(add(datetime(2000, 2, 28), days=2), datetime(2000, 3, 1))  # 加 2 天
        self.assertEqual(add(test_time, days=365), add(test_time, years=1))  # 加 1 年
        self.assertEqual(add(test_time, days=-365), add(test_time, years=-1))  # 减 1 年
        self.assertEqual(add(test_time, hours=1), datetime(2014, 10, 16, 1))  # 加 1 小时
        self.assertEqual(add(test_time, hours=-1), datetime(2014, 10, 15, 23))  # 减 1 小时
        self.assertEqual(add(test_time, minutes=1), datetime(2014, 10, 16, 0, 1))  # 加 1 分钟
        self.assertEqual(add(test_time, minutes=-1), datetime(2014, 10, 15, 23, 59))  # 减 1 分钟
        self.assertEqual(add(test_time, seconds=1), datetime(2014, 10, 16, 0, 0, 1))  # 加 1 秒
        self.assertEqual(add(test_time, seconds=-1), datetime(2014, 10, 15, 23, 59, 59))  # 减 1 秒
        # 特殊日期(闰月)
        self.assertEqual(add(datetime(2001, 1, 31), months=1), datetime(2001, 2, 28))
        self.assertEqual(add(datetime(2000, 1, 31), months=1), datetime(2000, 2, 29))
        self.assertEqual(add(datetime(2000, 2, 1), months=1), datetime(2000, 3, 1))
        self.assertEqual(add(datetime(2000, 2, 1), months=1, days=-1), datetime(2000, 2, 29))
        self.assertEqual(add(datetime(1999, 2, 1), years=1, months=1), datetime(2000, 3, 1))
        self.assertEqual(add(datetime(1999, 2, 1), years=1, months=1, days=-1), datetime(2000, 2, 29))
        self.assertEqual(add(datetime(2000, 2, 1), years=1, months=1, days=-1), datetime(2001, 2, 28))
        # 倍数计算
        self.assertEqual(add(test_time, years=1, number=2), datetime(2016, 10, 16))  # 加 1 年 * 2 倍
        self.assertEqual(add(test_time, years=-1, number=2), datetime(2012, 10, 16))  # 减 1 年 * 2 倍
        self.assertEqual(add(test_time, months=1, number=2), datetime(2014, 12, 16))  # 加 1 月 * 2 倍
        self.assertEqual(add(test_time, months=-1, number=2), datetime(2014, 8, 16))  # 减 1 月 * 2 倍
        self.assertEqual(add(datetime(2014, 9, 29), days=1, number=2), datetime(2014, 10, 1))  # 加 1 天 * 2 倍
        self.assertEqual(add(datetime(2014, 10, 1), days=-1, number=2), datetime(2014, 9, 29))  # 减 1 天 * 2 倍
        self.assertEqual(add(test_time, hours=1, number=2), datetime(2014, 10, 16, 2))  # 加 1 小时 * 2 倍
        self.assertEqual(add(test_time, hours=-1, number=2), datetime(2014, 10, 15, 22))  # 减 1 小时 * 2 倍
        self.assertEqual(add(test_time, hours=1, number=1.5), datetime(2014, 10, 16, 1, 30))  # 加 1 小时 * 1.5 倍

    # sub 测试
    def test_sub(self):
        zero_secends = _sub_dict()
        # 没差异判断
        self.assertEqual(sub(), zero_secends)  # 默认返回全是0
        self.assertEqual(sub(now(), now()), zero_secends)
        self.assertEqual(sub(None, now()), zero_secends)
        self.assertEqual(sub(now(), None), zero_secends)

        # 相差天数判断
        one_days = _sub_dict(days=1, sum_days=1, sum_seconds=24 * 60 * 60)  # 1 天的时间差
        self.assertEqual(sub(now(), now() - timedelta(days=1)), one_days)  # 相差 1 天
        t1 = now() + timedelta(days=1)
        self.assertEqual(sub(t1, now()), one_days)  # 相差 1 天
        self.assertEqual(sub(now(), t1), _sub_dict(days=-1, sum_days=-1, sum_seconds=-24 * 60 * 60))  # 相差 -1 天
        self.assertEqual(sub(now(), t1, abs=True), one_days)  # 绝对值相差 1 天

        # 时分秒判断
        self.assertEqual(sub(now(), now() - timedelta(hours=1)), _sub_dict(hours=1, sum_seconds=60 * 60))  # 相差 1 小时
        self.assertEqual(sub(now(), now() + timedelta(hours=2)), _sub_dict(hours=-2, sum_seconds=-2 * 60 * 60))
        self.assertEqual(sub(now(), now() + timedelta(hours=2), abs=True), _sub_dict(hours=2, sum_seconds=2 * 60 * 60))
        self.assertEqual(sub(now(), now() - timedelta(minutes=35)), _sub_dict(minutes=35, sum_seconds=35 * 60))
        self.assertEqual(sub(now(), now() + timedelta(minutes=32)), _sub_dict(minutes=-32, sum_seconds=-32 * 60))
        self.assertEqual(sub(now(), now() - timedelta(seconds=35)), _sub_dict(seconds=35, sum_seconds=35))  # 相差 35 秒
        self.assertEqual(sub(now(), now() + timedelta(seconds=32)), _sub_dict(seconds=-32, sum_seconds=-32))
        self.assertEqual(sub(now(), now() - timedelta(minutes=62)), _sub_dict(hours=1, minutes=2, sum_seconds=62 * 60))
        self.assertEqual(sub(now(), now() - timedelta(hours=2, minutes=3, seconds=2)),
                         _sub_dict(hours=2, minutes=3, seconds=2, sum_seconds=2 * 3600 + 3 * 60 + 2))  # 相差2时3分2秒
        self.assertEqual(sub(now(), now() + timedelta(hours=2, minutes=3, seconds=2)),
                         _sub_dict(hours=-2, minutes=-3, seconds=-2, sum_seconds=-(2 * 3600 + 3 * 60 + 2)))  # 相差2时3分2秒
        self.assertEqual(sub(now(), now() - timedelta(seconds=2.9)), _sub_dict(seconds=2, sum_seconds=2))  # 小数忽略

        # 年月判断
        res = sub(now(), now() - timedelta(days=32))
        self.assertEqual(res.get('sum_days'), 32)
        self.assertEqual(res.get('years'), 0)
        self.assertEqual(res.get('months'), 1)
        self.assertTrue(res.get('days') in (1, 2, 3, 4))
        self.assertEqual(res.get('hours'), 0)
        self.assertEqual(res.get('minutes'), 0)
        self.assertEqual(res.get('seconds'), 0)
        self.assertEqual(res.get('sum_seconds'), 32 * 24 * 60 * 60)

        res = _sub_dict(years=1, days=2, hours=1, seconds=53, sum_days=367, sum_seconds=367 * 24 * 60 * 60 + 3653)
        self.assertEqual(sub(datetime(2014, 12, 18, 11, 8, 6), datetime(2013, 12, 16, 10, 7, 13)), res)

        res = _sub_dict(years=-1, days=-2, hours=-1, seconds=-53, sum_days=-367, sum_seconds=-367 * 24 * 60 * 60 - 3653)
        self.assertEqual(sub(datetime(2013, 12, 16, 10, 7, 13), datetime(2014, 12, 18, 11, 8, 6)), res)

        res = _sub_dict(months=1, sum_days=31, sum_seconds=31 * 24 * 60 * 60)
        self.assertEqual(sub(datetime(2014, 8, 30), datetime(2014, 7, 30)), res)

        res = _sub_dict(months=1, days=1, sum_days=32, sum_seconds=32 * 24 * 60 * 60)
        self.assertEqual(sub(datetime(2014, 9, 16), datetime(2014, 8, 15)), res)

        res = _sub_dict(months=1, sum_days=30, sum_seconds=30 * 24 * 60 * 60)
        self.assertEqual(sub(datetime(2014, 10, 30), datetime(2014, 9, 30)), res)

        res = _sub_dict(days=30, sum_days=30, sum_seconds=30 * 24 * 60 * 60)
        self.assertEqual(sub(datetime(2014, 11, 1), datetime(2014, 10, 2)), res)

        res = _sub_dict(days=-30, sum_days=-30, sum_seconds=-30 * 24 * 60 * 60)
        self.assertEqual(sub(datetime(2014, 10, 2), datetime(2014, 11, 1)), res)

        # 特殊日期(闰月)
        res = _sub_dict(months=1, sum_days=29, sum_seconds=29 * 24 * 60 * 60)
        self.assertEqual(sub(datetime(2000, 3, 1), datetime(2000, 2, 1)), res)  # 闰月 29 天

        res = _sub_dict(months=1, sum_days=28, sum_seconds=28 * 24 * 60 * 60)
        self.assertEqual(sub(datetime(2001, 3, 1), datetime(2001, 2, 1)), res)  # 平月 28 天

        res = _sub_dict(years=1, months=1, sum_days=394, sum_seconds=394 * 24 * 60 * 60)
        self.assertEqual(sub(datetime(2000, 3, 1), datetime(1999, 2, 1)), res)  # 平月 28 天

    # get_datetime 测试
    def test_get_datetime(self):
        self.assertEqual(get_datetime("2017-9-5", "12:9:2"), datetime(2017, 9, 5, 12, 9, 2))
        self.assertEqual(get_datetime(date(2017, 9, 5), dt(13, 9, 52)), datetime(2017, 9, 5, 13, 9, 52))
        self.assertEqual(get_datetime("2017-9-5", dt(13, 9, 52)), datetime(2017, 9, 5, 13, 9, 52))
        self.assertEqual(get_datetime(date(2017, 9, 5), "12:9:2"), datetime(2017, 9, 5, 12, 9, 2))
        self.assertEqual(get_datetime("2014-02-06 12:09:00", '12:9:2'), datetime(2014, 2, 6, 12, 9, 2))
        # 没有 时分秒
        self.assertEqual(get_datetime("2017-9-5", '0:0:0'), datetime(2017, 9, 5))
        self.assertEqual(get_datetime("2017-9-5", None), datetime(2017, 9, 5))
        self.assertEqual(get_datetime("2017-9-5", ''), datetime(2017, 9, 5))
        # 错误类型
        self.assertEqual(get_datetime(None, "12:9:2"), None)
        self.assertEqual(get_datetime('', "12:9:2"), None)
        # timedelta 类型
        self.assertEqual(get_datetime("2017-9-5", timedelta()), datetime(2017, 9, 5, 0, 0, 0))
        self.assertEqual(get_datetime("2017-9-5", timedelta(0, 3602)), datetime(2017, 9, 5, 1, 0, 2))
        self.assertEqual(get_datetime("2017-9-5", timedelta(5, 3602)), datetime(2017, 9, 10, 1, 0, 2))
        self.assertEqual(get_datetime("2017-9-5", timedelta(0, -2)), datetime(2017, 9, 4, 23, 59, 58))

    # add_datetime_time 测试
    def test_add_datetime_time(self):
        test_time = dt(12, 9, 2)
        self.assertEqual(add_datetime_time(test_time), test_time)
        self.assertEqual(add_datetime_time('12:9:2'), test_time)
        self.assertEqual(add_datetime_time(test_time, hours=1, minutes=1, seconds=1), dt(13, 10, 3))
        self.assertEqual(add_datetime_time(test_time, seconds=3601), dt(13, 9, 3))
        self.assertEqual(add_datetime_time(test_time, minutes=61), dt(13, 10, 2))
        self.assertEqual(add_datetime_time(test_time, seconds=58), dt(12, 10, 0))
        self.assertEqual(add_datetime_time(test_time, seconds=-2), dt(12, 9, 0))
        self.assertEqual(add_datetime_time(test_time, seconds=-3), dt(12, 8, 59))
        self.assertEqual(add_datetime_time(test_time, seconds=-61), dt(12, 8, 1))
        self.assertEqual(add_datetime_time(test_time, minutes=51), dt(13, 0, 2))
        self.assertEqual(add_datetime_time(test_time, minutes=-9), dt(12, 0, 2))
        self.assertEqual(add_datetime_time(test_time, minutes=-3), dt(12, 6, 2))
        self.assertEqual(add_datetime_time(test_time, minutes=-61), dt(11, 8, 2))
        self.assertEqual(add_datetime_time(test_time, hours=11), dt(23, 9, 2))
        self.assertEqual(add_datetime_time(test_time, hours=12), dt(0, 9, 2))
        self.assertEqual(add_datetime_time(test_time, hours=13), dt(1, 9, 2))
        self.assertEqual(add_datetime_time(test_time, hours=-3), dt(9, 9, 2))
        self.assertEqual(add_datetime_time(test_time, hours=-11), dt(1, 9, 2))
        self.assertEqual(add_datetime_time(test_time, hours=-12), dt(0, 9, 2))
        self.assertEqual(add_datetime_time(test_time, hours=-13), dt(23, 9, 2))
        # 错误类型
        self.assertEqual(add_datetime_time(dt(), seconds=0), dt())
        self.assertEqual(add_datetime_time(None), None)
        self.assertEqual(add_datetime_time(''), None)
        self.assertEqual(add_datetime_time(12345), None)
        self.assertEqual(add_datetime_time("2014-02-06 12:09:00"), dt(12, 9, 0))
        # 不允许跨天
        self.assertEqual(add_datetime_time(test_time, hours=1, minutes=1, seconds=1, cross_day=False), dt(13, 10, 3))
        self.assertEqual(add_datetime_time(test_time, seconds=3601, cross_day=False), dt(13, 9, 3))
        self.assertEqual(add_datetime_time(test_time, minutes=61, cross_day=False), dt(13, 10, 2))
        self.assertEqual(add_datetime_time(test_time, seconds=58, cross_day=False), dt(12, 10, 0))
        self.assertEqual(add_datetime_time(test_time, seconds=-2, cross_day=False), dt(12, 9, 0))
        self.assertEqual(add_datetime_time(test_time, seconds=-3, cross_day=False), dt(12, 8, 59))
        self.assertEqual(add_datetime_time(test_time, seconds=-61, cross_day=False), dt(12, 8, 1))
        self.assertEqual(add_datetime_time(test_time, minutes=51, cross_day=False), dt(13, 0, 2))
        self.assertEqual(add_datetime_time(test_time, minutes=-9, cross_day=False), dt(12, 0, 2))
        self.assertEqual(add_datetime_time(test_time, minutes=-3, cross_day=False), dt(12, 6, 2))
        self.assertEqual(add_datetime_time(test_time, minutes=-61, cross_day=False), dt(11, 8, 2))

        self.assertEqual(add_datetime_time(test_time, hours=11, cross_day=False), dt(23, 9, 2))
        self.assertEqual(add_datetime_time(test_time, hours=12, cross_day=False), dt(23, 59, 59))
        self.assertEqual(add_datetime_time(test_time, hours=13, cross_day=False), dt(23, 59, 59))
        self.assertEqual(add_datetime_time(test_time, hours=-3, cross_day=False), dt(9, 9, 2))
        self.assertEqual(add_datetime_time(test_time, hours=-11, cross_day=False), dt(1, 9, 2))
        self.assertEqual(add_datetime_time(test_time, hours=-12, cross_day=False), dt(0, 9, 2))
        self.assertEqual(add_datetime_time(test_time, hours=-13, cross_day=False), dt(0, 0, 0))

    # sub_datetime_time 测试
    def test_sub_datetime_time(self):
        self.assertEqual(sub_datetime_time(dt(12, 9, 2), dt(12, 8, 0)), 62)
        self.assertEqual(sub_datetime_time(dt(12, 8, 0), dt(12, 9, 2)), -62)
        self.assertEqual(sub_datetime_time('12:9:2', '12:8:0'), 62)
        self.assertEqual(sub_datetime_time('12:8:0', '12:9:2'), -62)
        self.assertEqual(sub_datetime_time('0:0:0', '0:8:0'), -480)
        self.assertEqual(sub_datetime_time('8:8:0', '0:0:0'), 3600 * 8 + 480)
        # 错误类型
        self.assertEqual(sub_datetime_time(None, None), None)
        self.assertEqual(sub_datetime_time('8:8:0', None), None)
        self.assertEqual(sub_datetime_time('', '0:8:0'), None)

    def test_get_time_string(self):
        now = datetime.now()
        dtime1 = now - timedelta(days=123)
        ts = get_time_string(dtime1)
        self.assertEqual(ts, '4个月前')

        dtime1 = now - timedelta(days=370)
        ts = get_time_string(dtime1)
        self.assertEqual(ts, '1年前')

        dtime1 = now - timedelta(hours=26)
        ts = get_time_string(dtime1)
        self.assertEqual(ts, '1天前')

        dtime1 = now - timedelta(minutes=4)
        ts = get_time_string(dtime1)
        self.assertEqual(ts, '4分钟前')

        dtime1 = now - timedelta(seconds=10)
        ts = get_time_string(dtime1)
        self.assertEqual(ts, '刚刚')

        dtime1 = now - timedelta(minutes=4)
        ts = get_time_string(time.mktime(dtime1.timetuple()))
        self.assertEqual(ts, '4分钟前')

    # get_week_range 测试
    def test_get_week_range(self):
        # 默认时间
        today = date.today
        this_week_star, this_week_end = get_week_range(None)
        self.assertEqual(this_week_star, None)
        self.assertEqual(this_week_end, None)

        this_week_star, this_week_end = get_week_range(today())
        self.assertTrue(this_week_star <= today())
        self.assertTrue(this_week_end >= today())
        self.assertEqual(this_week_star.weekday(), 0)
        self.assertEqual(this_week_end.weekday(), 6)
        # 指定测试时间
        test_time = date(2016, 8, 2)
        test_week_star, test_week_end = get_week_range(test_time)
        self.assertEqual(test_week_star, date(2016, 8, 1))
        self.assertEqual(test_week_end, date(2016, 8, 7))
        # 指定测试时间
        test_time = date(2016, 8, 1)
        test_week_star, test_week_end = get_week_range(test_time)
        self.assertEqual(test_week_star, date(2016, 8, 1))
        self.assertEqual(test_week_end, date(2016, 8, 7))
        # 指定测试时间
        test_time = date(2016, 8, 7)
        test_week_star, test_week_end = get_week_range(test_time)
        self.assertEqual(test_week_star, date(2016, 8, 1))
        self.assertEqual(test_week_end, date(2016, 8, 7))

    # get_month_range 测试
    def test_get_month_range(self):
        # 指定测试时间
        test_month_star, test_month_end = get_month_range(2016, 8)
        self.assertEqual(test_month_star, date(2016, 8, 1))
        self.assertEqual(test_month_end, date(2016, 8, 31))
        # 指定测试时间(特殊月份，闰年2月)
        test_month_star, test_month_end = get_month_range(2016, 2)
        self.assertEqual(test_month_star, date(2016, 2, 1))
        self.assertEqual(test_month_end, date(2016, 2, 29))
        # 指定测试时间(特殊月份，平年2月)
        test_month_star, test_month_end = get_month_range(2015, 2)
        self.assertEqual(test_month_star, date(2015, 2, 1))
        self.assertEqual(test_month_end, date(2015, 2, 28))

    # get_month_list 测试
    def test_get_month_list(self):
        # 指定测试时间
        month_list = get_month_list(2016, 8)
        self.assertEqual(len(month_list), 31)
        self.assertEqual(month_list[0], date(2016, 8, 1))
        self.assertEqual(month_list[-1], date(2016, 8, 31))
        # 指定测试时间(特殊月份，闰年2月)
        month_list = get_month_list(2016, 2)
        self.assertEqual(len(month_list), 29)
        self.assertEqual(month_list[0], date(2016, 2, 1))
        self.assertEqual(month_list[-1], date(2016, 2, 29))
        # 指定测试时间(特殊月份，平年2月)
        month_list = get_month_list(2015, 2)
        self.assertEqual(len(month_list), 28)
        self.assertEqual(month_list[0], date(2015, 2, 1))
        self.assertEqual(month_list[-1], date(2015, 2, 28))

    # utc_2_local 测试
    def test_utc_2_local(self):
        utc_now = datetime.utcnow().replace(microsecond=0)
        local_now = now()
        self.assertNotEqual(local_now, utc_now)
        self.assertEqual(local_now, utc_2_local(utc_now))

    # local_2_utc 测试
    def test_local_2_utc(self):
        utc_now = datetime.utcnow().replace(microsecond=0)
        local_now = now()
        self.assertNotEqual(local_now, utc_now)
        self.assertEqual(local_2_utc(local_now), utc_now)

    # spend_time 测试
    def test_spend_time(self):
        self.assertEqual(spend_time(0), '')
        self.assertEqual(spend_time(10), '10秒')
        self.assertEqual(spend_time(60), '1分钟')
        self.assertEqual(spend_time(1000), '16分钟40秒')
        self.assertEqual(spend_time(3600), '1小时')
        self.assertEqual(spend_time(10000), '2小时46分钟40秒')
        self.assertEqual(spend_time(24*60*60), '1天')
        self.assertEqual(spend_time(100000), '1天3小时46分钟40秒')


if __name__ == "__main__":
    unittest.main()
