# -*- coding: utf-8 -*-

"""
    bello_adam.utils
    ~~~~~~~~~

    Utility functions and classes.

    :copyright: (c) 2017 by Nicola Iarocci.
    :license: BSD, see LICENSE for more details.
"""

import logging

from flask import current_app as app


logger = logging.getLogger(__name__)


class Config(object):
    """ Helper class used through the code to access configuration settings.
    If the main flaskapp object is not instantiated yet, returns the default
    setting in the bello_adam __init__.py module, otherwise returns the flaskapp
    config value (which value might override the static defaults).
    """
    def __getattr__(self, name):
        try:
            # will return 'working outside of application context' if the
            # current_app is not available yet
            return app.config.get(name)
        except:
            # fallback to the module-level default value
            return getattr(app, name)


# makes an instance of the Config helper class available to all the modules
config = Config()

