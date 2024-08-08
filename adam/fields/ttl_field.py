# -*- coding: utf-8 -*-
"""
TTL field
"""
import logging
from mongoengine.fields import BaseField
from datetime import datetime

logger = logging.getLogger(__name__)


class TTLField(BaseField):
    """A timedelta field.
    Looks to the outside world like a datatime.timedelta, but stores
    in the database as an integer (or float) number of seconds.
    """
    def __init__(self, valid_time, **kwargs):
        self.valid_time = valid_time
        super().__init__(**kwargs)

    def validate(self, value):
        return True

    def to_mongo(self, value):
        return value

    def __set__(self, instance, value):
        if not value:
            return
        if isinstance(value, str):
            instance._data[self.name] = {
                'value': value,
                'expired_at': datetime.now() + self.valid_time
            }
            instance._mark_as_changed(self.name)
        elif isinstance(value, dict):
            instance._data[self.name] = value
            instance._mark_as_changed(self.name)
        else:
            logger.warning('Unknow type to set %s', value)

    def to_python(self, value):
        if not value:
            return None
        if isinstance(value, dict):
            value['expired_at'] = value['expired_at'].isoformat()
            return value
        return value
