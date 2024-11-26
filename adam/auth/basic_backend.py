# -*- coding: utf-8 -*-

from flask import request, Response, current_app as app, g, abort


class BasicBackend(object):
    # One-time configuration and initialization.

    def set_mongo_prefix(self, value):
        g.mongo_prefix = value

    def get_mongo_prefix(self):
        return g.get('mongo_prefix')

    def set_request_auth_value(self, value):
        g.auth_value = value

    def get_request_auth_value(self):
        return g.get('auth_value')

    def get_user_or_token(self):
        return g.get('user')

    def set_user_or_token(self, user):
        g.user = user

    def get_credential(self):
        raise NotImplementedError

    def authenticate(self, credential, allowed_roles, resource, method):
        """ This function is called to check if a username / password
        combination is valid. Must be overridden with custom logic.

        :param credential:
        :param allowed_roles: allowed user roles.
        :param resource: resource being requested.
        :param method: HTTP method being executed (POST, GET, etc.)
        """
        return True

    def render_error_wrong_credential(self):
        """ Returns a standard a 401 response that enables basic auth.
        Override if you want to change the response and/or the realm.
        """
        resp = Response(None, 401, {'WWW-Authenticate': 'Basic realm="%s"' %
                                    __package__})
        abort(401, description='Please provide proper credentials',
              response=resp)

    def lookup_license(self, key=None, user_id=None):
        """attach license if need"""
        license_db = app.data.driver.db['license']
        license_obj = None
        if user_id:
            license_obj = license_db.find_one({'user_id': user_id})
        elif key:
            license_obj = license_db.find_one({'key': key})
        if license_obj:
            request.license = license_obj
        return license_obj

    def authorized(self, allowed_roles, resource, method):
        """ Validates the the current request is allowed to pass through.

        :param allowed_roles: allowed roles for the current request, can be a
                              string or a list of roles.
        :param resource: resource being requested.
        """
        credential = self.get_credential()
        if credential:
            return self.authenticate(credential, allowed_roles, resource, method)

        return False
