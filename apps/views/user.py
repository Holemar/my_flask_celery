# -*- coding:utf-8 -*-
"""
user view
"""

import logging

from mongoengine.queryset.visitor import Q
from flask import current_app as app, request

from adam.exceptions import BaseError
from adam.views import ResourceView, Blueprint
from apps.models.enums import UserEnum

bp = Blueprint(__name__)
LOGGER = logging.getLogger(__name__)


class User(ResourceView):
    """User view.

    默认已经加上的请求地址：
 <Rule '/api/user' (GET, OPTIONS, HEAD) -> |collection_read|user|>,
 <Rule '/api/user' (OPTIONS, POST) -> |collection_create|user|>,
 <Rule '/api/user/count' (GET, OPTIONS, HEAD) -> |collection_count|user|>,
 <Rule '/api/user/import' (OPTIONS, POST) -> |collection_import|user|>,
 <Rule '/api/user/<id>' (GET, OPTIONS, HEAD) -> |item_read|user|>,
 <Rule '/api/user/<id>' (PUT, OPTIONS) -> |item_update|user|>,
 <Rule '/api/user/<id>' (OPTIONS, DELETE) -> |item_delete|user|>,
 <Rule '/api/user/batch' (PUT, OPTIONS) -> |batch_update|user|>,
 <Rule '/api/user/batch' (OPTIONS, DELETE) -> |batch_delete|user|>,
 <Rule '/api/user/<id>/default_project' (OPTIONS, POST) -> |item_reference_create|user|default_project>,
 <Rule '/api/user/<id>/default_project' (GET, OPTIONS, HEAD) -> |item_reference_read|user|default_project>,
 <Rule '/api/user/<id>/default_project' (OPTIONS, DELETE) -> |item_reference_delete|user|default_project>,
 <Rule '/api/user/<id>/projects' (OPTIONS, POST) -> |item_relation_create|user|projects>,
 <Rule '/api/user/<id>/projects/count' (GET, OPTIONS, HEAD) -> |item_relation_count|user|projects>,
 <Rule '/api/user/<id>/projects' (GET, OPTIONS, HEAD) -> |item_relation_read|user|projects>,

    下面自定义的请求地址：
 <Rule '/api/user/<id>/remove' (OPTIONS, DELETE) -> |item@remove|user|>,
 <Rule '/api/user/<id>/delete' (OPTIONS, DELETE) -> |item@delete|user|>,
 <Rule '/api/user/<id>/completion' (OPTIONS, POST) -> |item@completion|user|>,
 <Rule '/api/user/login' (OPTIONS, POST) -> |collection@login|user|>,
 <Rule '/api/user/logout' (OPTIONS, POST) -> |collection@logout|user|>,
 <Rule '/api/user/register' (OPTIONS, POST) -> |collection@register|user|>,
    """

    @bp.static_method('login', methods=['POST'])
    def login(self):
        """
        @api {POST} /api/user/login 用户登陆
        @apiExample Example usage:
        curl -X POST \
          http://localhost:5000/api/user/login \
          -H 'Cache-Control: no-cache' \
          -H 'Content-Type: application/json' \
          -H 'Postman-Token: 185f886d-5f85-4d92-8d2f-e76edfd3e126' \
          -d '{
            "mobile": "17666107315",
            "password": "107315"
        }'
        """
        data = request.get_json()
        user_name = data.get('user_name')
        password = data.get('password')

        if not password or not user_name:
            BaseError.param_miss()

        query = Q(user_name=user_name) | Q(email=user_name) | Q(mobile=user_name)
        user = self.model.objects(is_delete__ne=True).filter(query).first()
        if (not user) or (not user.check_password(password)):
            BaseError.param_error('账号或者密码错误')

        # generate session
        session_model = app.models["Session"]
        if app.config.get('SINGLE_LOGIN'):
            sessions = session_model.objects(user=user.id, permanent__ne=1, is_delete__ne=True)
            for session in sessions:
                session.soft_delete()
        session = session_model.generate(user, user_type=session_model.user_type.enum.USER)
        data = {
            'user': user,
            'token': session.token,
            'default_project': user.default_project.id if user.default_project else None
        }
        return data

    @bp.static_method('logout', methods=['POST'])
    def logout(self):
        """注销."""
        if request.session:
            request.session.delete()
            request.session = None
        return {}

    @bp.static_method('register', methods=['POST'])
    def register(self):
        """
        @api {POST} /api/user/register 用户注册
        @apiExample Example usage:
        curl -X POST \
          http://localhost:5000/api/user/signup \
          -H 'Cache-Control: no-cache' \
          -H 'Content-Type: application/json' \
          -d '{
            "mobile": "13005458903",
            "code": "190873",
            "invite_code": "5b56a0f790f56065fc2b0c47"
        }'
        """
        session_model = app.models['Session']
        user_model = app.models['User']
        data = request.get_json()
        user_name = data.get('user_name')
        email = data.get('email')
        mobile = data.get('mobile')
        password = data.get('password')
        user_type = UserEnum.USER

        if not user_name:
            BaseError.param_miss()
        if not password:
            BaseError.param_miss()

        query = Q(user_name=user_name)
        user = self.model.objects().filter(is_delete__ne=True).filter(query).first()
        if user:
            BaseError.param_error('该用户名已存在，请另外注册')

        if mobile:
            m_query = Q(mobile=mobile)
            user = self.model.objects().filter(is_delete__ne=True).filter(m_query).first()
            if user:
                BaseError.param_error('该号码已被注册，请另外注册')
        if email:
            e_query = Q(email=email)
            user = self.model.objects().filter(is_delete__ne=True).filter(e_query).first()
            if user:
                BaseError.param_error('该邮箱已被注册，请另外注册')

        user = user_model()
        user.user_name = data.get('user_name')
        user.nickname = data.get('nickname')
        user.email = email
        user.mobile = mobile
        user.password = password
        user.user_type = user_type
        user.save()

        session = session_model.generate(user, user_type)
        data = {
            'user': user,
            'token': session.token,
            'default_project': user.default_project.id if user.default_project else None
        }
        return data

    @bp.item_method('remove', methods=['DELETE'])
    def remove(self, instance):
        """
        @api {DELETE} /api/user/:id/remove 移除一个账号(软删除)
        @apiParam {string} id 用户ID
        @apiExample Example usage:
        curl -X DELETE \
          http://localhost:5000/api/user/5b163ba190f560c5c968564d/remove \
          -H 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.xxx.oo7emt6fqgrv-FgLqPQArRk11DrJWIXRtEMDYW5NFTA' \
          -H 'Content-Type: application/json'
        """
        app.models['Session'].objects(user=instance.id).delete()
        instance.soft_delete()
        return {'deleted': True}

    @bp.item_method('delete', methods=['DELETE'])
    def delete(self, instance):
        """
        @api {DELETE} /api/user/:id/delete 删除用户
        @apiName UserDelete
        """
        app.models['Session'].objects(user=instance.id).delete()
        app.models['User'].objects(id=instance.id).delete()
        return {}

    @bp.item_method('completion', methods=['POST'])
    def completion(self, instance):
        """
        @api {POST} /api/user/:id/completion 补全信息
        @apiParam {string} id 待补全用户的ID
        @apiExample Example usage:
        curl -X POST \
          http://localhost:5000/api/user/5b163ba190f560c5c968564d/completion \
          -H 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.xxx.oo7emt6fqgrv-FgLqPQArRk11DrJWIXRtEMDYW5NFTA' \
          -H 'Content-Type: application/json' \
          -d '{
            "mobile": "123632864872",
            "email": "test@xxx.com"
        }'
        """
        data = request.get_json()
        instance.user_name = data.get('user_name') or instance.user_name
        instance.nickname = data.get('nickname') or instance.nickname
        instance.mobile = data.get('mobile') or instance.mobile
        instance.email = data.get('email') or instance.email
        instance.save()
        return {}

