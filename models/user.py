# -*- coding:utf-8 -*-

from adam.documents import ResourceDocument, BaseError
from adam.fields import (StringField, EmailField, PasswordField, EnumField, BooleanField, LazyReferenceField,
                         RelationField, DictField)
from .enums import UserEnum, Language


class User(ResourceDocument):
    """用户Model."""

    meta = {
        'hidden': ['password'],
        # 'allow_inheritance': True,
        'search_fields': ['email', 'mobile'],
        "included_fields": ["email", "mobile", "name"]
    }

    # 姓名
    user_name = StringField()
    nickname = StringField()  # 昵称

    email = EmailField()  # 邮箱
    mobile = StringField()  # 手机号码
    password = PasswordField()  # 密码
    user_type = EnumField(enum=UserEnum, default=UserEnum.USER)
    language = EnumField(enum=Language, default=Language.CHINESE)  # 语言偏好

    default_project = LazyReferenceField(document_type='Project', db_field='default_project_id')  # 用户默认的项目
    projects = RelationField(document_type='Project', relation_type='has_many', target_field='user')  # 用户有权限的项目

    # 是否删除。用来标记该用户是否被删除了
    is_delete = BooleanField()
    others = DictField(default={})  # 数据迁移时的临时存储信息

    def check_password(self, password):
        """检查密码hash.

            param: password 需要比对的密码
            return:
                Boolean, True/False
        """
        if not self.password:
            return False
        return self._fields['password'].check_password(self.password, password)

    def change_password(self, password):
        """更改密码.

            param: password 需要更改的密码
            return:
                Boolean, True/False
        """
        self.password = self._fields['password'].generate_password(password)
        return True

    def soft_delete(self):
        if self.is_delete:
            BaseError.user_deleted('该用户已经被删除，请勿重复删除')
        self.is_delete = True
        self.save()
        return True

    def has_permission(self, endpoint, instance=None):
        """检查用户是否有权限访问某个接口."""
        return True
