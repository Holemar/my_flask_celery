# -*- coding:utf-8 -*-

from utils.documents import ResourceDocument
from utils.fields import StringField, BooleanField, LazyReferenceField, DictField


class Project(ResourceDocument):
    """Project Model."""

    meta = {}

    name = StringField()  # 项目名称
    description = StringField()  # 项目简单描述，不是任务描述
    # requirement = StringField()  # 项目需求

    user = LazyReferenceField(document_type='User', db_field='user_id')

    # app是针对某个场景特殊开发的一系列model和etl、web_api, 没有项目都属于某种app，
    # app_name是根目录下app/下某个app的目录名，比如/app/month_report,则此处填写month_report
    app_name = StringField(default='info_assistant')

    # 是否删除。用来标记该用户是否被删除了
    is_delete = BooleanField()
    others = DictField(default={})  # 数据迁移时的临时存储信息

