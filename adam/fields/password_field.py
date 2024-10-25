# -*- coding: utf-8 -*-
"""
密码字段
"""

import hashlib
from mongoengine.fields import BaseField
from abc import ABCMeta, abstractmethod
from ..utils.rc4 import encode as rc4_encode, decode as rc4_decode
from ..utils.config_util import config


class IPassword(metaclass=ABCMeta):
    @abstractmethod
    def generate_password(self, password):
        pass

    def to_mongo(self, value):
        """加密，储存字段值"""
        return self.generate_password(value)

    def to_python(self, value):
        """解密，获取字段值"""
        return value

    def check_password(self, pw_hash, password):
        if not pw_hash:
            return False
        return self.generate_password(password) == pw_hash


class MD5PasswordImpl(IPassword):
    def __init__(self, *args, **kwargs):
        # 加密 key 值
        SECRET_SALT = config.PASSWORD_SECRET or config.JWT_SECRET or 'be9xj6u6eg0la3o2zv5rs8khu7fa0av1'
        self.salt = kwargs.get('salt', SECRET_SALT)

    def generate_password(self, password):
        hash = hashlib.md5((self.salt + password).encode('utf-8')).hexdigest()
        return hash


class RC4PasswordImpl(IPassword):
    def __init__(self, *args, **kwargs):
        # 加密 key 值
        SECRET_SALT = config.PASSWORD_SECRET or config.JWT_SECRET or 'be9xj6u6eg0la3o2zv5rs8khu7fa0av1'
        self.salt = kwargs.get('salt', SECRET_SALT)

    def generate_password(self, password):
        secret_txt = rc4_encode(password, self.salt)
        return secret_txt

    def to_python(self, value):
        """解密，获取字段值"""
        return rc4_decode(value, self.salt)


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
        """解密，获取字段值"""
        # 避免new实例时异常，如 Model(username='oaxxx', password="password123")
        try:
            return self.impl.to_python(value)
        except Exception as e:
            # 解密失败，可能是直接传入明文
            return value

    def generate_password(self, password):
        return self.impl.generate_password(password)

    def check_password(self, pw_hash, password):
        # 可能已经解码(从数据库读取出来会自动解码)
        if pw_hash == password:
            return True
        return self.impl.check_password(pw_hash, password)
