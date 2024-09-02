# -*- coding: utf-8 -*-
import os
from flask import current_app as app


class Config(object):
    """ Helper class used through the code to access configuration settings.
    If the main flaskapp object is not instantiated yet, returns the default
    setting in the flask_app __init__.py module, otherwise returns the flaskapp
    config value (which value might override the static defaults).
    """
    def __getattr__(self, name):
        try:
            # will return 'working outside of application context' if the
            # current_app is not available yet
            return app.config.get(name)
        except:
            # fallback to the module-level default value
            return os.environ.get(name)


# makes an instance of the Config helper class available to all the modules
config = Config()

