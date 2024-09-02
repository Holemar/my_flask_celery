# -*- coding:utf-8 -*-
import datetime
from mongoengine.fields import StringField, DateTimeField

from ..documents import ResourceDocument


class WorkStatus(ResourceDocument):
    """本 Model 用于记录 beat 及 worker 的运行状况"""
    meta = {
        # 'db_alias': 'broker',
    }

    name = StringField(unique=True)

    # 上次运行时间
    last_run_time = DateTimeField()

    @classmethod
    def now_run(cls, name):
        """设置当前运行状态"""
        obj = cls.objects(name=name).first()
        if not obj:
            obj = cls(name=name)
        obj.last_run_time = datetime.datetime.now()
        # 有低概率的并发写入导致主键冲突
        try:
            obj.save()
        except:
            pass

    @classmethod
    def is_run(cls, name, timeout):
        """查看当前运行状态
        当上次运行时间还没超过 超时时间(timeout) 则返回 True，否则返回 False
        """
        obj = cls.objects(name=name).first()
        if not obj or not obj.last_run_time:
            return False
        # 计算距离上次运行时间
        now = datetime.datetime.now()
        timedelta = now - obj.last_run_time
        sum_days = timedelta.days
        sum_seconds = timedelta.seconds + sum_days * 24 * 60 * 60
        return sum_seconds < timeout

    @classmethod
    def run_names(cls, name, timeout):
        """查看当前运行正常的记录
        当上次运行时间还没超过 超时时间(timeout) 则累加1，否则不计算
        """
        # 计算距离上次运行时间
        now = datetime.datetime.now()
        objects = cls.objects(name__startswith=name).all()
        result = []
        for obj in objects:
            if not obj.last_run_time:
                try:
                    obj.delete()
                except:
                    pass
                continue
            timedelta = now - obj.last_run_time
            sum_days = timedelta.days
            sum_seconds = timedelta.seconds + sum_days * 24 * 60 * 60
            if sum_seconds < timeout:
                result.append(obj.name)
            else:
                try:
                    obj.delete()
                except:
                    pass
        return result


