# -*- coding: utf-8 -*-
"""
密码字段
"""

import hashlib
from mongoengine.fields import BaseField
from abc import ABCMeta, abstractmethod
from utils.rc4 import encode as rc4_encode


class IPassword(metaclass=ABCMeta):
    @abstractmethod
    def generate_password(self, password):
        pass

    def to_mongo(self, value):
        return self.generate_password(value)

    def to_python(self, value):
        return value

    def check_password(self, pw_hash, password):
        if not pw_hash:
            return False
        return self.generate_password(password) == pw_hash


class MD5PasswordImpl(IPassword):
    def __init__(self, *args, **kwargs):
        self.salt = kwargs.get('salt', '')

    def generate_password(self, password):
        hash = hashlib.md5((self.salt + password).encode('utf-8')).hexdigest()
        return hash


class RC4PasswordImpl(IPassword):
    def __init__(self, *args, **kwargs):
        self.salt = kwargs.get('salt', '')

    def generate_password(self, password):
        secret_txt = rc4_encode(password, self.salt)
        return secret_txt


class PasswordField(BaseField):
    """A timedelta field.
    Looks to the outside world like a datatime.timedelta, but stores
    in the database as an integer (or float) number of seconds.
    """
    IMPLEMENTATION = {
        'rc4': RC4PasswordImpl,
        'md5': MD5PasswordImpl,
    }

    def __init__(self, *args, **kwargs):
        # self.enum = enum
        # kwargs['choices'] = [choice for choice in enum]
        super().__init__(*args, **kwargs)
        self.impl = self.IMPLEMENTATION[kwargs.get('impl', 'rc4')](*args, **kwargs)

    def validate(self, value):
        pass
        # if not isinstance(value, (timedelta, int, float)):
        #     self.error(u'cannot parse timedelta "%r"' % value)

    def to_mongo(self, value):
        # encrypted...
        return self.impl.to_mongo(value)

    def to_python(self, value):
        return self.impl.to_python(value)

    def generate_password(self, password):
        return self.impl.generate_password(password)

    def check_password(self, pw_hash, password):
        return self.impl.check_password(pw_hash, password)
