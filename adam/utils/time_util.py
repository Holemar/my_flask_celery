#!python
# -*- coding:utf-8 -*-
"""
公用函数(时间处理)
Created on 2014/10/16
Updated on 2022/02/21
@author: Holemar
"""
import re
import time
import datetime
import calendar
import logging

__all__ = ('add', 'sub', 'to_string', 'to_time', 'to_datetime', 'to_date', 'to_timestamp', 'to_datetime_time',
           'datetime_time_to_str', 'is_dst', 'add_datetime_time', 'sub_datetime_time', 'get_datetime', 'get_week_range',
           'get_month_range', 'get_month_list', 'get_time_string', 'calculate_age', 'utc_2_local', 'local_2_utc',
           'spend_time')

DEFAULT_FORMAT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
DEFAULT_DATE_FORMAT = '%Y-%m-%d'  # 默认日期格式
DEFAULT_MONTH_FORMAT = '%Y-%m'  # 默认月份格式
DEFAULT_TIME_FORMAT = '%H:%M:%S'
FORMAT_LIST = (DEFAULT_FORMAT, '%Y-%m-%d %H:%M:%S.%f', DEFAULT_DATE_FORMAT, DEFAULT_MONTH_FORMAT,
               '%Y年%m月%d日 %H时%M分%S秒', '%Y年%m月%d日　%H时%M分%S秒', '%Y年%m月%d日 %H时%M分', '%Y年%m月%d日　%H时%M分',
               '%Y年%m月%d日 %H:%M:%S', '%Y年%m月%d日　%H:%M:%S', '%Y年%m月%d日 %H:%M', '%Y年%m月%d日　%H:%M', '%Y年%m月%d日',
               '%Y/%m/%d %H:%M:%S', '%Y/%m/%d %H:%M:%S.%f', '%Y/%m/%d', '%Y%m%d', '%Y%m%d%H%M%S',
               '%Y/%m/%d %H:%M', '%Y-%m-%d %H:%M', "%Y-%m-%dT%H:%M",
               '%Y-%m-%d %p %I:%M:%S', '%Y-%m-%d %p %I:%M', '%Y/%m/%d %p %I:%M:%S', '%Y/%m/%d %p %I:%M',
               "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S+08:00", "%Y-%m-%dT%H:%M:%S.%f+08:00",
               )

# fix py3
try:
    long
except NameError:
    long = int
    basestring = str
    unicode = str

# hour,minute,second,microsecond format
time_re = re.compile(
    r'(?P<hour>\d{1,2}):(?P<minute>\d{1,2})'
    r'(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?'
)
# all time format
datetime_re = re.compile(
    r'(?P<year>\d{4})[-/](?P<month>\d{1,2})[-/](?P<day>\d{1,2})'
    r'([T ](?P<hour>\d{1,2}):(?P<minute>\d{1,2})'
    r'(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?'
    r'(?P<tzinfo>Z|[+-]\d{2}(?::?\d{2})?)?'
    r')?$'
)


def to_string(value=None, format_str=None, default_now=False):
    """
    change a time to str
    :param {time|datetime.datetime|datetime.date|int|long|float|string} value: original time
    :param {string} format_str: the return format of time. (default format: %Y-%m-%d %H:%M:%S)
    :param {bool} default_now: True: when value is None return now, False: when value is None return None.
    :return {string}: the string time
    """
    this_format = format_str
    if this_format is None:
        this_format = DEFAULT_FORMAT

    if value in (None, ''):
        if default_now is False:
            return None
        value = datetime.datetime.now()
        return value.strftime(this_format)
    # datetime
    elif isinstance(value, datetime.datetime):
        return value.strftime(this_format)
    # datetime.date
    elif isinstance(value, datetime.date):
        if format_str is None:
            this_format = DEFAULT_DATE_FORMAT
        return value.strftime(this_format)
    # time
    elif isinstance(value, time.struct_time):
        return time.strftime(this_format, value)
    # string, change type first
    elif isinstance(value, basestring):
        value = _str_2_datetime(value)
        return value.strftime(this_format)
    # number, treated as a timestamp
    elif isinstance(value, (int, long, float)):
        value = _number_2_datetime(value)
        return value.strftime(this_format)
    # datetime.timedelta, change type first
    elif isinstance(value, datetime.timedelta):
        value = _timedelta_2_datetime(value)
        return value.strftime(this_format)
    # datetime.time
    elif isinstance(value, datetime.time):
        if format_str is None:
            this_format = DEFAULT_TIME_FORMAT
        return value.strftime(this_format)
    return None


def to_time(value=None, default_now=False, from_format=None):
    """
    change other type of time to type(time)
    :param {time|datetime.datetime|datetime.date|int|long|float|string} value: time of other type
    :param {bool} default_now: True: when value is None return now, False: when value is None return None.
    :param {string} from_format: when input value is str, use this format to get time(default format: %Y-%m-%d %H:%M:%S)
    :return {time.struct_time}: the type(time) of time
    """
    if value in (None, ''):
        if default_now is False:
            return None
        return time.localtime()
    # datetime, datetime.date
    elif isinstance(value, (datetime.datetime, datetime.date)):
        return value.timetuple()
    # time
    elif isinstance(value, time.struct_time):
        return value
    # string, change type first
    elif isinstance(value, basestring):
        value = _str_2_datetime(value, from_format=from_format)
        return value.timetuple()
    # number, treated as a timestamp
    elif isinstance(value, (int, long, float)):
        return time.localtime(value)
    # datetime.timedelta, change type first
    elif isinstance(value, datetime.timedelta):
        value = _timedelta_2_datetime(value)
        return value.timetuple()
    return None


def to_datetime(value=None, default_now=False, from_format=None):
    """
    change other type of time to type(datetime.datetime)
    note: from type(time) to type(datetime.datetime), can not keep microsecond
    :param {time|datetime.datetime|datetime.date|int|long|float|string} value: time of other type
    :param {bool} default_now: True: when value is None return now, False: when value is None return None.
    :param {string} from_format: when input value is str, use this format to get time(default format: %Y-%m-%d %H:%M:%S)
    :return {datetime.datetime}: the type(datetime.datetime) of time
    """
    if value in (None, ''):
        if default_now is False:
            return None
        return datetime.datetime.now()
    # datetime
    elif isinstance(value, datetime.datetime):
        return value
    # datetime.date (different from datetime.datetime, it has not hour, minute and second)
    elif isinstance(value, datetime.date):
        return datetime.datetime(value.year, value.month, value.day)
        # return datetime.datetime.combine(value, datetime.datetime.min.time())
    # time
    elif isinstance(value, time.struct_time):
        return datetime.datetime(*value[:6])
    # string
    elif isinstance(value, basestring):
        return _str_2_datetime(value, from_format=from_format)
    # number, treated as a timestamp
    elif isinstance(value, (int, long, float)):
        return _number_2_datetime(value)
    # datetime.timedelta, change type first
    elif isinstance(value, datetime.timedelta):
        return _timedelta_2_datetime(value)
    return None


def to_date(value=None, default_now=False, from_format=None):
    """
    change other type of time to type(datetime.date)
    :param {time|datetime.datetime|datetime.date|int|long|float|string} value: time of other type
    :param {bool} default_now: True: when value is None return now, False: when value is None return None.
    :param {string} from_format: when input value is str, use this format to get time(default format: %Y-%m-%d %H:%M:%S)
    :return {datetime.date}: the type(datetime.date) of time
    """
    if value in (None, ''):
        if default_now is False:
            return None
        return datetime.date.today()
    # datetime
    elif isinstance(value, datetime.datetime):
        # return datetime.date(value.year, value.month, value.day)
        return value.date()
    # datetime.date, note: isinstance(datetime.datetime(), datetime.date) is True
    elif isinstance(value, datetime.date):
        return value
    # time
    elif isinstance(value, time.struct_time):
        return datetime.date(*value[:3])
    # string, change type first
    elif isinstance(value, basestring):
        value = _str_2_datetime(value, from_format=from_format)
        return value.date()
    # number, treated as a timestamp
    elif isinstance(value, (int, long, float)):
        return datetime.date.fromtimestamp(value)
    # datetime.timedelta, change type first
    elif isinstance(value, datetime.timedelta):
        value = _timedelta_2_datetime(value)
        return value.date()
    return None


def to_timestamp(value=None, from_format=None, default_now=False):
    """
    change time to timestamp(unit: second)
    :param {time|datetime.datetime|datetime.date|int|long|float|string} value: original time
    :param {bool} default_now: True: when value is None return now, False: when value is None return None.
    :param {string} from_format: when input value is str, use this format to get time(default format: %Y-%m-%d %H:%M:%S)
    :return {float}: timestamp(unit: second)
    """
    if value in (None, ''):
        if default_now is False:
            return None
        return time.time()
    # datetime
    elif isinstance(value, datetime.datetime):
        return value.timestamp()
    # datetime.date
    elif isinstance(value, datetime.date):
        return time.mktime(value.timetuple())
    # time
    elif isinstance(value, time.struct_time):
        return time.mktime(value)
    # str
    elif isinstance(value, basestring):
        value = _str_2_datetime(value, from_format=from_format)
        return value.timestamp()
    # number, treated as a timestamp
    elif isinstance(value, (int, long, float)):
        return value
    # datetime.timedelta
    elif isinstance(value, datetime.timedelta):
        return value.days * 24 * 60 * 60 + value.seconds + (value.microseconds / 1000000.0)
    return None


def _str_2_datetime(value, from_format=None):
    """
    字符串转成时间
    :param {string} value: 原时间
    :param {string} from_format: 原时间对应的格式字符串(默认为: %Y-%m-%d %H:%M:%S)
    :return {datetime.datetime}: 对应的时间
    """
    if from_format:
        return datetime.datetime.strptime(value, from_format)

    match = datetime_re.match(value)
    if match:
        kw = match.groupdict()
        if kw['microsecond']:
            kw['microsecond'] = kw['microsecond'].ljust(6, '0')
        kw.pop('tzinfo')  # utc not support
        kw = dict([(k, int(v)) for k, v in kw.items() if v is not None])
        return datetime.datetime(**kw)

    # try to fix Chinese
    global FORMAT_LIST
    if '上午' in value: value = value.replace('上午', 'AM')
    if u'上午' in value: value = value.replace(u'上午', 'AM')
    if '下午' in value: value = value.replace('下午', 'PM')
    if u'下午' in value: value = value.replace(u'下午', 'PM')
    for format in FORMAT_LIST:
        try:
            return datetime.datetime.strptime(value, format)
        except:
            pass

    raise ValueError("time data %r does not match time format" % value)


def _number_2_datetime(value):
    """
    纯数值类型转成时间
    :param {int|long|float} value: 原时间
    :return {datetime.datetime}: 对应的时间
    """
    return datetime.datetime.fromtimestamp(value)


def _timedelta_2_datetime(value):
    """
    datetime.timedelta类型转成时间
    :param {datetime.timedelta} value: 原时间
    :return {datetime.datetime}: 对应的时间
    """
    # datetime.timedelta 类型，则从初始时间相加减得出结果
    return datetime.datetime.fromtimestamp(0) + value


def to_datetime_time(value):
    """
    将时间转成 datetime.time 类型
    :param {datetime.time|datetime.datetime|string} value: 时间字符串
    :return {datetime.time}: 对应的时间
    """
    if value in ('', None):
        return None
    if isinstance(value, basestring):
        match = time_re.match(value)
        if match:
            kw = match.groupdict()
            if kw['microsecond']:
                kw['microsecond'] = kw['microsecond'].ljust(6, '0')
            new_kw = {}
            for k, v in kw.items():
                if v is not None:
                    new_kw[k] = int(v)
            return datetime.time(**new_kw)
        else:
            value = to_datetime(value)
    # datetime.time
    if isinstance(value, datetime.time):
        return value
    # datetime.datetime
    elif isinstance(value, datetime.datetime):
        return datetime.time(value.hour, value.minute, value.second)
    # datetime.timedelta
    elif isinstance(value, datetime.timedelta):
        seconds = value.seconds
        hour = seconds // 3600
        minute = (seconds % 3600) // 60
        second = seconds % 60
        return datetime.time(hour, minute, second)
    return None


def datetime_time_to_str(value, format_str='%H:%M:%S'):
    """
    datetime.time 时间类型，转成前端需要的字符串
    :param {datetime.time|string} value: 时间
    :param {string} format_str: 日期格式化的格式字符串(默认为: %Y-%m-%d %H:%M:%S)
    :return {string}: 时间字符串
    """
    value = to_datetime_time(value)
    if value is None:
        return None
    return value.strftime(format_str)


def is_dst(value=None, from_format=None):
    """
    判断传入时间是否夏令时
    :param {time|datetime.datetime|datetime.date|int|long|float|string} value: 需判断的时间(为空则默认为当前时间；纯数值则认为是时间戳,单位:秒)
    :param {string} from_format: 日期格式化的格式字符串(默认为: %Y-%m-%d %H:%M:%S)
    :return {bool}: 是否夏令时
    """
    _time = to_time(value=value, from_format=from_format)
    return bool(_time.tm_isdst) if _time is not None else False


def add(original_time=None, years=0, months=0, days=0, hours=0, minutes=0, seconds=0, number=1):
    """
    添加时间
    :param {time|datetime.datetime|datetime.date|int|long|float|string} original_time: 原时间(为空则默认为当前时间；纯数值则认为是时间戳,单位:秒)
    :param {int} years: 要添加多少年
    :param {int} months: 要添加多少个月
    :param {int} days: 要添加多少天 (允许负数表示减多少天)
    :param {int} hours: 要添加多少小时 (允许负数表示减多少小时)
    :param {int} minutes: 要添加多少分钟 (允许负数表示减多少分钟)
    :param {int} seconds: 要添加多少秒 (允许负数表示减多少秒)
    :param {int} number: 倍数(默认1个,如果值为2表示所有添加时间是其它时间参数的2倍)
    :return {datetime}: 添加完时间后的时间
    """
    after_time = to_datetime(original_time)
    if after_time is None:
        logging.debug("时间参数无法解析:%s" % original_time)
        return None

    # 添加倍数
    if number != 1:
        years *= number
        months *= number
        days *= number
        hours *= number
        minutes *= number
        seconds *= number
    # 系统自带有的添加时间
    if days != 0:
        after_time += datetime.timedelta(days=days)
    if hours != 0:
        after_time += datetime.timedelta(hours=hours)
    if minutes != 0:
        after_time += datetime.timedelta(minutes=minutes)
    if seconds != 0:
        after_time += datetime.timedelta(seconds=seconds)
    if not (years or months):
        return after_time
    # 年、月的添加,系统没有自带函数,只能另外计算
    original_months_count = after_time.year * 12 + after_time.month - 1  # 原日期共经历了多少个月
    after_months_count = original_months_count + months  # 添加后日期，共经历了多少个月
    after_year = int(after_months_count / 12 + years)  # 添加后的年份
    after_month = int(after_months_count % 12 + 1)  # 添加后的月份
    after_day = min(after_time.day, calendar.monthrange(after_year, after_month)[1])  # 添加后的日期
    # 最终时间
    return after_time.replace(year=after_year, month=after_month, day=after_day)


def sub(time1=None, time2=None, abs=False):
    """
    求出两个时间的差
    :param {time|datetime.datetime|datetime.date|int|long|float|string} time1: 被减时间(为空则默认为当前时间；纯数值则认为是时间戳,单位:秒)
    :param {time|datetime.datetime|datetime.date|int|long|float|string} time2: 减去时间(为空则默认为当前时间；纯数值则认为是时间戳,单位:秒)
    :param {bool} abs: 是否返回两个时间的差的绝对值。为 True 则返回绝对值；否则直接 time1 减去 time2, 默认False
    :return {dict}: 返回两个时间的差
       下面返回的各值都是整形。
       如两时间相差1年2个月,返回的值大概是 {'years' : 1, 'months' : 2, 'days' : 0, 'hours' : 0, 'minutes' : 0, 'seconds' : 0,'sum_days':791, 'sum_seconds':791*24*60*60}
       返回值为:
        {
            'years' : 0, # {int} 两时间相差多少年
            'months' : 0, # {int} 两时间相差多少个月,去掉前面年的部分
            'days' : 0, # {int} 两时间相差多少天,去掉前面年、月的部分
            'hours' : 0, # {int} 两时间相差多少小时,去掉前面年、月、日的部分
            'minutes' : 0, # {int} 两时间相差多少分钟,去掉前面年、月、日、时的部分
            'seconds' : 0, # {int} 两时间相差多少秒,去掉前面年、月、日、时、分的部分
            'sum_days' : 0 # {int} 两时间相差多少天,这是独立值,不包括其它参数的内容
            'sum_seconds' : 0 # {int} 两时间相差多少秒,这是独立值,不包括其它参数的内容
        }
    """
    # 参数转成 datetime 类型
    time1 = to_datetime(time1)
    time2 = to_datetime(time2)
    # 返回值
    res = {'years': 0, 'months': 0, 'days': 0, 'hours': 0, 'minutes': 0, 'seconds': 0, 'sum_days': 0, 'sum_seconds': 0}
    if time1 is None or time2 is None:
        logging.debug("时间参数无法解析, time1:%s, time2:%s" % (time1, time2))
        return res
    # 如果两时间相等,没必要再判断了
    if time1 == time2:
        return res
    plus = time1 > time2  # 正数标识, 正数时为 True
    _time1 = time1 if plus else time2
    _time2 = time2 if plus else time1
    timedelta = time1 - time2 if plus else time2 - time1  # 时间差
    # sum_days、sum_seconds 的差值计算
    sum_days = res['sum_days'] = timedelta.days
    sum_seconds = res['sum_seconds'] = timedelta.seconds + sum_days * 24 * 60 * 60
    # 时、分、秒 的差值计算
    res['seconds'] = sum_seconds % 60
    res['minutes'] = (sum_seconds % 3600) // 60
    res['hours'] = (sum_seconds % (24 * 60 * 60)) // 3600
    # 年、月、日 的差值计算
    months_count1 = _time1.year * 12 + _time1.month - 1  # 日期1共经历了多少个月
    months_count2 = _time2.year * 12 + _time2.month - 1  # 日期2共经历了多少个月
    months_count = months_count1 - months_count2
    days = res['days'] = _time1.day - _time2.day
    if days < 0 and months_count > 0:
        res['days'] += calendar.monthrange(_time2.year, _time2.month)[1]
        months_count -= 1
    res['years'] = months_count // 12
    res['months'] = months_count % 12
    # 本身是正数或者要求绝对值的,不用判断负值
    if plus or abs:
        return res
    # 负数处理
    for k, v in res.items():
        res[k] = -v
    return res


def add_datetime_time(time_value, hours=0, minutes=0, seconds=0, cross_day=True):
    """
    添加时间
    :param {datetime.time|string} time_value: 时间
    :param {int} hours: 加上多少小时(用负数表示减去)
    :param {int} minutes: 加上多少分钟(用负数表示减去)
    :param {int} seconds: 加上多少秒(用负数表示减去)
    :param {bool} cross_day: 是否允许跨天(为True则加减之后返回值会是变成前一天或者后一天的值，为False则超出当天最大值时取当天的最大值)
    :return {datetime.time}:计算后的时间
    """
    value = to_datetime_time(time_value)
    if value is None: return None

    if seconds != 0:
        second = value.second + seconds
        # 超过60的秒数
        if second >= 60 or second <= -60:
            minutes += second // 60
            second %= 60
        # 负数处理
        if second < 0:
            second += 60
            minutes -= 1
        value = value.replace(second=second)
    if minutes != 0:
        minute = value.minute + minutes
        # 超过60的分钟数
        if minute >= 60 or minute <= -60:
            hours += minute // 60
            minute %= 60
        # 负数处理
        if minute < 0:
            minute += 60
            hours -= 1
        value = value.replace(minute=minute)
    if hours != 0:
        hour = value.hour + hours
        # 允许跨天情况
        if cross_day:
            # 超过24的小时数
            if hour >= 24 or hour <= -24:
                hour %= 24
            # 负数处理
            if hour < 0:
                hour += 24
        else:
            # 超过24的小时数
            if hour >= 24:
                return datetime.time(23, 59, 59)
            # 负数处理
            if hour < 0:
                return datetime.time(0, 0, 0)

        value = value.replace(hour=hour)

    return value


def sub_datetime_time(time1, time2):
    """
    两时间相差多少秒，只精确到秒
    :param {datetime.time|string} time1: 时间1
    :param {datetime.time|string} time2: 时间2
    :return {int}: 两时间相差的秒数(当 time2 大于 time1 时返回负数)
    """
    time1 = to_datetime_time(time1)
    time2 = to_datetime_time(time2)
    # 错误类型输入，需要避免认为两个值相等
    if time1 is None or time2 is None:
        return None
    hour = time1.hour - time2.hour
    minute = time1.minute - time2.minute
    second = time1.second - time2.second
    return hour * 3600 + minute * 60 + second


def get_datetime(datetime_date, datetime_time):
    """
    将日期和时间，合并成一个
    :param {datetime.date} datetime_date: 指定日期(必须有值，为空则返回空)
    :param {datetime.time|string} datetime_time: 指定时间(没有传值则算做 00:00:00 时间)
    :return {datetime.datetime}: 返回指定日期指定时间的 datetime.datetime 类型时间
    """
    if datetime_date in ("", None):
        return None
    result = to_datetime(datetime_date)
    if result is None:
        return None
    # datetime.timedelta
    if isinstance(datetime_time, datetime.timedelta):
        return result + datetime_time
    datetime_time = to_datetime_time(datetime_time)
    if datetime_time is None:
        return result
    return result.replace(hour=datetime_time.hour, minute=datetime_time.minute, second=datetime_time.second)


def get_time_string(unix_time):
    """获取指定时间距离现在多久的字符串
    :param {time|datetime.datetime|datetime.date|int|long|float|string} unix_time: 原始时间(必须比现在小)
    :return {string}: 时间距离现在多久
    """
    if not isinstance(unix_time, (int, long, float)):
        unix_time = int(to_timestamp(unix_time))

    nowtime = int(time.time())
    delta = int(nowtime - unix_time)

    min_seconds = 60
    hour_seconds = 60 * min_seconds
    day_seconds = 24 * hour_seconds
    mon_seconds = 30 * day_seconds
    year_seconds = 12 * mon_seconds

    minutes = delta // min_seconds
    hour = delta // hour_seconds
    day = delta // day_seconds
    mon = delta // mon_seconds
    year = delta // year_seconds

    if year > 0:
        return "%s年前" % year
    if mon > 0:
        return "%s个月前" % mon
    if day > 0:
        return "%s天前" % day
    if hour > 0:
        return "%s小时前" % hour
    if minutes > 0:
        return "%s分钟前" % minutes
    return "刚刚"


def calculate_age(born):
    """计算年龄"""
    born = to_date(born)
    today = datetime.date.today()
    try:
        birthday = born.replace(year=today.year)
    except ValueError:  # raised when birth date is February 29 and the current year is not a leap year
        birthday = born.replace(year=today.year, day=born.day - 1)
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year


def get_week_range(date):
    """
    获取指定日期所在的星期的开始日期及结束日期
    :param {time|datetime|int|long|float|string} date: 原时间(为空则默认为当前时间；纯数值则认为是时间戳,单位:秒)
    :return {tuple<datetime.date, datetime.date>}: 对应的星期的开始日期及结束日期
    """
    if date in ("", None):
        return None, None
    date = to_datetime(date)
    this_weekday = date.weekday()
    start_date = add(date, days=-this_weekday) if this_weekday > 0 else date  # 星期一
    end_date = add(date, days=6 - this_weekday) if this_weekday < 6 else date  # 星期天
    return to_date(start_date), to_date(end_date)


def get_month_range(year, month):
    """
    获取指定日期所在的月的开始日期及结束日期
    :param {int} year: 年份
    :param {int} month: 月份
    :return {tuple<datetime.date, datetime.date>}: 对应的月的开始日期及结束日期
    """
    end_day = calendar.monthrange(year, month)[1]
    return datetime.date(year, month, 1), datetime.date(year, month, end_day)


def get_month_list(year, month):
    """
    获取指定年月的日期列表
    :param {int} year: 年份
    :param {int} month: 月份
    :return {list<datetime.date>}: 对应的日期列表
    """
    end_day = calendar.monthrange(year, month)[1]
    return [datetime.date(year, month, day) for day in range(1, end_day + 1)]


def utc_2_local(utc_value):
    """
    UTC 时间转本地时间（ +8:00 ）
    :param {time|datetime|int|long|float|string} utc_value: UTC 时间
    :return {datetime.datetime}: 本地时间
    """
    utc_value = to_datetime(utc_value)
    if utc_value is None:
        return None
    local_tm = datetime.datetime.fromtimestamp(0)
    utc_tm = datetime.datetime.utcfromtimestamp(0)
    offset = local_tm - utc_tm
    return utc_value + offset


def local_2_utc(local_value):
    """
    本地时间转 UTC 时间（ -8:00 ）
    :param {time|datetime|int|long|float|string} local_value: 本地时间
    :return {datetime.datetime}: UTC 时间
    """
    local_value = to_datetime(local_value)
    if local_value is None:
        return None
    return datetime.datetime.utcfromtimestamp(local_value.timestamp())


def spend_time(second):
    """
    显示花费了多少时间
    :param {int} second: 所花费的时间(秒)
    :return {str}: 方便人看的时间(天、时、秒)
    """
    minute_second = 60
    hour_second = 60 * 60
    day_second = 24 * hour_second
    left_seconds = second
    show = []
    # 花了多少天
    use_days = left_seconds // day_second
    if use_days:
        show.append(str(use_days) + '天')
        left_seconds = left_seconds % day_second
    # 花了多少小时
    use_hours = left_seconds // hour_second
    if use_hours:
        show.append(str(use_hours) + '小时')
        left_seconds = left_seconds % hour_second
    # 花了多少分钟
    use_minutes = left_seconds // minute_second
    if use_minutes:
        show.append(str(use_minutes) + '分钟')
        left_seconds = left_seconds % minute_second
    # 剩下多少秒(去掉分钟、小时、天之后的)
    if left_seconds:
        show.append(str(left_seconds) + '秒')
    return ''.join(show)
