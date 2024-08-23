# -*- coding: utf-8 -*-

import os
import logging
from flask import request, current_app as app, abort
import jwt
from .basic_backend import BasicBackend

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
            abort(500, description='Server error, missing secret')

        if request.args.get('token'):
            credential = request.args['token']
        elif request.headers.get('Authorization'):
            credential = request.headers.get('Authorization').strip()
            if credential.lower().startswith(('token', 'bearer')):
                credential_list = credential.split(' ')
                if len(credential_list) != 2:
                    abort(401, description='Invalid jwt token')
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
                    request.user = user_mode.objects.first()
                else:
                    session_object = session_model.objects(token=credential).first()
                    if session_object:
                        if session_object.is_delete is True:
                            abort(401, description='token does not exists')
                        request.credential = credential
                        jwt_object = jwt.decode(credential, secret, algorithms=[jwt_alg])
                        request.jwt = jwt_object
                        request.session = session_object
                        user = user_mode.objects(id=session_object.user.id).first()
                        request.user = user
                    # else:
                    #     abort(401, description='token does not exists')
            except (jwt.DecodeError, jwt.ExpiredSignatureError) as ex:
                logger.error('jwt decode error: %s', str(ex))
                abort(401, description='Invalid jwt token')

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

