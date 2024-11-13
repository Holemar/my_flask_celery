# -*- coding: utf-8 -*-

import os
import logging

import jwt
from flask import request, current_app as app, abort

from .basic_backend import BasicBackend
from ..documents import BaseError
from ..utils.config_util import config

logger = logging.getLogger(__name__)
_env = os.environ.get('ENV') or 'development'


class TokenBackend(BasicBackend):
    """
        token based auth.
    """
    def get_credential(self):
        credential = None
        secret = app.config.get('JWT_SECRET')
        jwt_alg = app.config.get('JWT_ALG') or 'HS256'
        if not secret or not jwt_alg:
            BaseError.system_error('Server error, missing secret')

        if request.args.get('token'):
            credential = request.args['token']
        elif request.headers.get('Authorization'):
            credential = request.headers.get('Authorization').strip()
            if credential.lower().startswith(('token', 'bearer')):
                credential_list = credential.split(' ')
                if len(credential_list) != 2:
                    BaseError.unauthorized('Invalid jwt token')
                credential = credential_list[1]

        # 初始化
        request.jwt = None
        request.user = None
        request.company = None
        request.session = None
        request.language = request.headers.get('language')  # 语言值，如: chinese
        request.timezone_value = int(request.headers.get('timezone') or 0)  # 时区值，如: 8
        request.timezone = request.headers.get('timezonestr') or config.TIME_ZONE  # 时区字符串，如: Asia/Shanghai

        if credential:
            try:
                session_model = app.models['Session']
                user_mode = app.models['User']
                company_mode = app.models['Company']

                # magic admin key
                if _env in ('development', 'dev') and credential == 'XXX':
                    request.user = user_mode.objects.first()
                else:
                    session_object = session_model.objects(token=credential).first()
                    if session_object:
                        if session_object.is_delete is True:
                            BaseError.unauthorized('token does not exists')
                        request.credential = credential
                        jwt_object = jwt.decode(credential, secret, algorithms=[jwt_alg])
                        request.jwt = jwt_object
                        request.session = session_object
                        user = user_mode.objects(id=session_object.user.id).first()
                        request.user = user
                        if not request.language and hasattr(user, 'language'):
                            request.language = user.language.value
                        if user and user.company:
                            company = company_mode.objects(id=user.company.id).first()
                            if company:
                                if company.is_delete:
                                    BaseError.unauthorized('company does not exists')
                                elif company.has_expired():
                                    BaseError.unauthorized('company has expired')
                            request.company = company
                    # else:
                    #     BaseError.unauthorized('token does not exists')
            except (jwt.DecodeError, jwt.ExpiredSignatureError) as ex:
                logger.warning('jwt decode error: %s', str(ex))
                BaseError.unauthorized('Invalid jwt token')

        return credential

    def authenticate(self, credential, allowed_roles, resource, method):
        """ This function is called to check if a token is valid. Must be
        overridden with custom logic.  Default behavior, pass if jwt is verified.

        :param credential: decoded user name.
        :param allowed_roles: allowed user roles
        :param resource: resource being requested.
        :param method: HTTP method being executed (POST, GET, etc.)
        """
        # user = request.user
        # jwt_object = request.jwt
        # session = request.session
        return True

