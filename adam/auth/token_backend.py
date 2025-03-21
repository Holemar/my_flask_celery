# -*- coding: utf-8 -*-

import os
import logging

import jwt
from flask import request, current_app as app

from .basic_backend import BasicBackend
from ..exceptions import BaseError
from ..utils.config_util import config

logger = logging.getLogger(__name__)
_env = os.environ.get('ENV') or 'development'


class TokenBackend(BasicBackend):
    """
        token based auth.
    """
    def get_credential(self):
        credential = None
        secret = config.JWT_SECRET
        jwt_alg = config.JWT_ALG or 'HS256'
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
        request.session = None

        if credential:
            try:
                session_model = app.models['Session']
                user_mode = app.models['User']

                # magic admin key
                if _env in ('development', 'dev') and credential == 'XXX':
                    user = request.user = user_mode.objects.first()
                    if user:
                        request.session = session_model.objects(user=user).order_by('-id').first()
                        if not request.session:
                            request.session = session_model.generate(user)
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

