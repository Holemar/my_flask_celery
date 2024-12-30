# -*- coding: utf-8 -*-

import logging

from flask import current_app as app, request
from adam.exceptions import BaseError
from adam.views import ResourceView, Blueprint

bp = Blueprint(__name__)
logger = logging.getLogger(__name__)


class Log(ResourceView):
    """Log view.
    注意这里的约定： view 类名必须跟 model 类名一致，会产生自动路由。如： Log view 类名对应 model 类名 Log，则会自动生成路由： /api/log/。
    另外，一个 view 文件，只能写一个 view 类，不能写多个(仅加载最后一个)。 view 文件名没约定，但建议跟 model 的文件名保持一致。

    默认已经加上的请求地址：
 <Rule '/api/log' (GET, OPTIONS, HEAD) -> |collection_read|log|>,
 <Rule '/api/log' (OPTIONS, POST) -> |collection_create|log|>,
 <Rule '/api/log/count' (GET, OPTIONS, HEAD) -> |collection_count|log|>,
 <Rule '/api/log/import' (OPTIONS, POST) -> |collection_import|log|>,
 <Rule '/api/log/<id>' (GET, OPTIONS, HEAD) -> |item_read|log|>,
 <Rule '/api/log/<id>' (PUT, OPTIONS) -> |item_update|log|>,
 <Rule '/api/log/<id>' (OPTIONS, DELETE) -> |item_delete|log|>,
 <Rule '/api/log/batch' (PUT, OPTIONS) -> |batch_update|log|>,
 <Rule '/api/log/batch' (OPTIONS, DELETE) -> |batch_delete|log|>,

    下面自定义的请求地址：
<Rule '/api/log/test' (GET, OPTIONS, HEAD, POST) -> |collection@test|log|>,
<Rule '/api/log/<id>/remove' (OPTIONS, DELETE) -> |item@remove|log|>,
    """

    acl = [  # 需要控制权限的 action 列表
        'collection_create',
        'item_update',
    ]

    @bp.static_method('test', methods=['GET', 'POST'], permissions=True)
    def get_fields_and_sources(self):
        """
        bp.static_method   # 静态方法
           第一个参数，接口名，可以自定义，但必须唯一
           methods 参数，请求方法，可以是GET、POST、PUT、DELETE等，可以多个
           permissions 参数，权限验证，True表示需要登录及权限验证，False表示不需要登录或者权限验证，不填这参数表示不需要权限验证

        请求url： {POST 请求} /api/log/test
        """
        get_data = request.args  # 获取 GET 请求的 参数
        get_value1 = get_data.get("key1", default=None, type=int)
        get_value2 = get_data.get("get_key2")

        post_data = request.form  # 获取 POST form 请求的 参数
        post_value1 = post_data.get("post_key1", default=None, type=str)
        post_value2 = post_data.get("post_key2")

        get_post_data = request.values  # 获取 GET及POST 请求的 参数
        all_value1 = get_post_data.get("all_key1", default=None, type=str)
        all_value2 = get_post_data.get("all_key2")

        header_data = request.headers  # 获取请求头的 参数
        head_value1 = header_data.get("head_key1", default=None, type=str)
        head_value2 = header_data.get("head_key2")

        json_data = request.get_json()  # 获取 POST 请求的 json 数据(如果请求的不是json数据，会抛出异常: werkzeug.exceptions.UnsupportedMediaType)
        user_name = json_data.get('user_name')

        # 当前登录的 user、session 对象
        user = request.user
        session = request.session
        project = session.project if session else None

        # 本类查询
        db_data = self.model.objects().filter(is_delete__ne=True).filter(user_name=user_name).first()

        # 自定义错误信息
        if not db_data:
            """
            接口自定义错误信息的3种写法：
            1. BaseError.data_not_exist("xxx资源不存在")  # 自定义 message 的写法
            2. raise BaseError.data_not_exist  # 使用默认 message 的写法
            3. BaseError.data_not_exist()  # 使用圆括号的写法，等同于写法 2，只是不需要写 raise
            """
            BaseError.data_not_exist()


    @bp.item_method('remove', methods=['DELETE'])
    def remove(self, instance):
        """
        bp.static_method   # 类方法
           第一个参数，接口名，可以自定义，但必须唯一
           methods 参数，请求方法，可以是GET、POST、PUT、DELETE等，可以多个
           permissions 参数，权限验证，True表示需要登录及权限验证，False表示不需要登录或者权限验证，不填这参数表示不需要权限验证

        请求url {DELETE 请求} /api/log/:id/remove 移除一行记录
        """
        instance.delete()
        return {'deleted': True}
