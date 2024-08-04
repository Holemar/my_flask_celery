# -*- coding:utf-8 -*-
"""
user view
"""

import os
import logging

from flask import current_app as app, request, abort
from utils.views import ResourceView, Blueprint


bp = Blueprint(__name__)
LOGGER = logging.getLogger(__name__)
_env = os.environ.get('ENV') or 'develop'


class User(ResourceView):
    """User view."""

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
    @bp.static_method('login', methods=['POST'])
    def login(self):
        """手机号码登录"""
        data = request.get_json()
        user_name = data.get('user_name')
        email = data.get('email')
        mobile = data.get('mobile')
        password = data.get('password')

        if password:
            if user_name:
                user = self.model.objects(user_name=user_name, is_delete__ne=True).first()
            elif mobile:
                user = self.model.objects(mobile=mobile, is_delete__ne=True).first()
            elif email:
                user = self.model.objects(email=email, is_delete__ne=True, class_check=False).first()
            if (not user) or (not user.check_password(password)):
                abort(400, '账号或者密码错误')
        else:
            abort(400, '参数错误')

        # generate session
        session_model = app.models["Session"]
        if app.config.get('SINGLE_LOGIN'):
            sessions = session_model.objects(user=user.id, permanent__ne=1, is_delete__ne=True)
            for session in sessions:
                session.soft_delete()
        session = session_model.generate(user, user_type=session_model.user_type.enum.USER)
        return session

    @bp.static_method('logout', methods=['POST'])
    def logout(self):
        """注销."""
        if request.session:
            request.session.delete()
            request.session = None
        return {}

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
    @bp.static_method('register', methods=['POST'])
    def register(self):
        """注册."""
        session_model = app.models['Session']
        user_model = app.models['User']
        data = request.get_json()
        user_name = data.get('user_name')
        email = data.get('email')
        mobile = data.get('mobile')
        password = data.get('password')
        user_type = data.get('user_type')

        if not mobile and not user_name and not email:
            abort(400, '参数错误')
        if not password:
            abort(400, '参数错误')

        user = user_model()
        user.user_name = data.get('user_name')
        user.nickname = data.get('nickname')
        user.email = email
        user.mobile = mobile
        user.password = password
        user.user_type = user_type
        user.save()

        session = session_model.generate(user, user_type)
        return session

    """
    @api {GET} /api/user/:id/remove 移除一个账号(软删除)
    @apiParam {string} id 用户ID
    @apiExample Example usage:
    curl -X DELETE \
      http://localhost:5000/api/user/5b163ba190f560c5c968564d/remove \
      -H 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.xxx.oo7emt6fqgrv-FgLqPQArRk11DrJWIXRtEMDYW5NFTA' \
      -H 'Content-Type: application/json'
    """
    @bp.item_method('remove', methods=['DELETE'])
    def remove(self, instance):
        app.models['Session'].objects(user=instance.id).delete()
        instance.soft_delete()
        return {'deleted': True}

    """
    @api {POST} /api/user/:id/delete 删除用户
    @apiName UserDelete
    """
    @bp.item_method('delete', methods=['DELETE'])
    def delete(self, instance):
        app.models['Session'].objects(user=instance.id).delete()
        app.models['User'].objects(id=instance.id).delete()
        return {}

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
    @bp.item_method('completion', methods=['POST'])
    def completion(self, instance):
        data = request.get_json()
        instance.user_name = data.get('user_name') or instance.user_name
        instance.nickname = data.get('nickname') or instance.nickname
        instance.mobile = data.get('mobile') or instance.mobile
        instance.email = data.get('email') or instance.email
        instance.save()
        return {}

