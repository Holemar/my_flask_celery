# -*- coding: utf-8 -*-

"""
Session
"""
from datetime import timedelta, datetime

import jwt
from flask import current_app as app

from adam.documents import ResourceDocument
from adam.fields import StringField, LazyReferenceField, EnumField, IntField, BooleanField
from .enums import UserEnum


class Session(ResourceDocument):
    """Session Model."""

    # user/manager
    user = LazyReferenceField(document_type='User', db_field='user_id')
    project = LazyReferenceField(document_type='Project', db_field='project_id')

    # token
    token = StringField(required=True)

    # token
    user_type = EnumField(enum=UserEnum, default=UserEnum.USER)

    # 1: stands for not deletable (manual generate)
    permanent = IntField()

    is_delete = BooleanField()

    @staticmethod
    def cache_key(user):
        return f"token:{user.id}"

    def soft_delete(self):
        self.is_delete = True
        self.save()
        return {"code": 0, "message": "", "data": {}}

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        return result

    @classmethod
    def generate(cls, user, user_type, expire_timedelta=None):
        """
        生成session
        """
        td = expire_timedelta or timedelta(days=7)
        exp = datetime.utcnow() + td
        jwt_object = {'user_id': str(user.id), 'mobile': user.mobile, 'email': user.email,
                      'user_type': user_type.value, 'exp': exp}
        token = jwt.encode(jwt_object, app.config.get('JWT_SECRET'), algorithm='HS256').decode()
        session = cls(user=user, token=token, user_type=user_type).save()
        return session
