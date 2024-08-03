# -*- coding: utf-8 -*-
"""
    flask 启动文件
    ~~~~~~~~~~~~

    This module implements the central WSGI application object as a Flask
    subclass.

    :copyright: (c) 2024 by Holemar Feng<daillow@gmail.com>.
"""
import fnmatch
import os
import sys
import logging
import importlib
import inspect
import re
import csv
import argparse
import json

from flask import Flask
from werkzeug.routing import BaseConverter
import click

from utils import celery_util
import bello_adam
import bello_adam.auth
from bello_adam.io.elastic import Elastic
from bello_adam.io.neo4j import Neo4j
from bello_adam.utils import api_prefix, extract_key_values, discovery_items_in_package, import_submodules, \
    load_rbac_policy
from celery import Celery, current_app, Task
from celery.schedules import crontab
from mongoengine import register_connection
from bello_adam import ResourceView, ResourceDocument, GraphDocument, Service, Middleware
from bello_adam.cos_connection import register_source
from bello_adam.log_filter import WerkzeugLogFilter

import bello_adam.models
import bello_adam.views
import bello_adam.services
import bello_adam.middlewares


logger = logging.getLogger('utils.flask_app')


def underscore(word):
    """
    Make an underscored, lowercase form from the expression in the string.

    Example::

        >>> underscore("DeviceType")
        "device_type"

    As a rule of thumb you can think of :func:`underscore` as the inverse of
    :func:`camelize`, though there are cases where that does not hold::

        >>> camelize(underscore("IOError"))
        "IoError"

    """
    word = re.sub(r"([A-Z]+)([A-Z][a-z])", r'\1_\2', word)
    word = re.sub(r"([a-z\d])([A-Z])", r'\1_\2', word)
    word = word.replace("-", "_")
    return word.lower()


class RegexConverter(BaseConverter):
    """ Extend werkzeug routing by supporting regex for urls/API endpoints """

    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


class Adam(Flask):
    #: Allowed methods for resource endpoints
    supported_resource_methods = ['GET', 'POST', 'DELETE']

    #: Allowed methods for item endpoints
    supported_item_methods = ['GET', 'PATCH', 'DELETE', 'PUT']

    def __init__(self, import_name=__package__, root='', settings='settings.py', task_path='tasks',
                 enable_celery=False, static_folder='static', template_folder='templates',
                 url_converters=None, media=None, model_path='models', view_path='views', **kwargs):
        """  main WSGI app is implemented as a Flask subclass. Since we want
        to be able to launch our API by simply invoking Flask's run() method,
        we need to enhance our super-class a little bit.
        """
        logging.getLogger('werkzeug').addFilter(WerkzeugLogFilter())

        cur_dir = os.path.dirname(__file__)
        logger.info('Init Adam2')
        self.current_file_dir = os.path.abspath(cur_dir)
        self.root = root or os.getcwd()  # 当前目录
        if isinstance(settings, str):
            settings = os.path.abspath(os.path.join(self.root, settings))
            logger.info('use setting %s', settings)

        service_path = 'services'
        middleware_path = 'middlewares'
        if root:
            # 引入项目根目录以及lib跟目录
            sys.path.append(".")
            sys.path.append("./" + root)
            model_path = root + '/models'
            view_path = root + '/views'
            service_path = root + '/services'
            middleware_path = root + '/middlewares'

        kwargs['template_folder'] = template_folder
        kwargs['static_folder'] = static_folder

        super().__init__(import_name, **kwargs)
        # self.validator = validator
        self.settings = settings

        self.load_config()
        self.myconfigs = {}

        # name
        self.name = self.config.get('APP_NAME') or 'default'

        # enable regex routing
        self.url_map.converters['regex'] = RegexConverter

        # optional url_converters and json encoder
        if url_converters:
            self.url_map.converters.update(url_converters)

        # Register mongoengine connections
        for k, v in self.config.get('MONGO_CONNECTIONS', {}).items():
            register_connection(alias=k, host=v)

        self.views = {}
        self.models = {}
        self.services = {}
        self.middlewares = {}
        self.tasks = {}

        # 加载model
        self.load_models(model_path)

        # 加载view
        self.load_views(view_path)

        load_middlewares = [
            'TokenMiddleware',
            'RateLimitMiddleware',
            'CorsMiddleware'
        ]
        for oth_midd in self.config.get('MIDDLEWARS', []):
            if oth_midd not in load_middlewares:
                load_middlewares.append(oth_midd)
        self.available_middlewares = []
        self.load_middleware(middleware_path)

        # 加载自定义中间件
        for middleware in load_middlewares:
            if middleware in self.middlewares:
                self.available_middlewares.append(self.middlewares[middleware])
                logger.debug('Register middleware %s', middleware)
            else:
                logger.error('unregistered middleware %s', middleware)

        self.media = media(self) if media else None

        self.load_service(service_path)
        self.load_build_in_commands()

        self.auth_backends = []
        for ab in self.config.get('AUTHENTICATION_BACKENDS') or ['utils.auth.TokenBackend']:
            auth_module = importlib.import_module(ab)
            is_class_member = lambda member: inspect.isclass(member) and member.__module__ == auth_module.__name__
            clsmembers = inspect.getmembers(auth_module, is_class_member)
            self.auth_backends.append(clsmembers[0][1]())

        if enable_celery:
            self.celery = Celery(self.name)
            self.celery.config_from_object(self.config.get('CeleryConfig'))

            celery_util.load_task(task_path)  # 加载 tasks 目录下的任务
            celery_util.load_task_schedule(os.path.join(self.root, task_path, 'schedule.json'))  # 加载定时任务

            task_schedule_path = os.path.join(root, task_path, 'schedule.json')
            if os.path.exists(task_schedule_path):
                self.load_task_schedule(task_schedule_path)

        for k, s in self.services.items():
            logger.debug('service on_loaded trigger %s', k)
            s.on_loaded()

    def pasrse_cron(self, cron):
        """
        parse cron format to celery cron
        http://www.nncron.ru/help/EN/working/cron-format.htm
        <Minute> <Hour> <Day_of_the_Month> <Month_of_the_Year> <Day_of_the_Week>
        """
        if type(cron) is str:
            minute, hour, day_of_month, month_of_year, day_of_week = cron.split(' ')
            return crontab(minute=minute, hour=hour, day_of_month=day_of_month, day_of_week=day_of_week,
                           month_of_year=month_of_year)
        else:
            return cron

    def load_task_schedule(self, path):
        if not os.path.exists(path):
            return
        schedule = {}
        with open(path, 'r') as reader:
            rules = json.load(reader)
            for r_task in rules:
                name = r_task['name']
                task = r_task['task']
                cron = self.pasrse_cron(r_task['cron'])
                schedule[name] = {
                    'task': task,
                    'schedule': cron
                }
        self.celery.conf.beat_schedule = schedule

    def load_config_csv(self, path):
        """
        Load json config file in app config
        """
        if path not in self.myconfigs:
            config = None
            config_path = os.path.join(self.root, 'config', path)
            if os.path.exists(config_path):
                with open(config_path, 'r') as reader:
                    self.myconfigs[path] = csv.reader(reader)

        return self.myconfigs.get(path)

    def load_config_json(self, path):
        """
        Load json config file in app config
        """
        if path not in self.myconfigs:
            config = None
            config_path = os.path.join(self.root, 'config', path)
            if os.path.exists(config_path):
                with open(config_path, 'r') as reader:
                    self.myconfigs[path] = json.load(reader)

        return self.myconfigs.get(path)

    def load_build_in_commands(self):
        """
        Load all build-in commands
        """
        commands = discovery_items_in_package(
            'bello_adam.commands', lambda x: isinstance(x, click.core.Command))
        for _k, _c in commands:
            logger.debug('Load command: %s', _k)
            self.cli.add_command(_c)

    def run(self, debug=None, **options):
        parser = argparse.ArgumentParser()
        parser.add_argument('-m', '--mode', choices=['route', 'api', 'worker', 'beat', 'monitor', 'shell'])
        parser.add_argument('-p', '--pool', choices=['solo', 'gevent', 'prefork', 'eventlet'], default='solo')
        parser.add_argument('-c', '--concurreny', default='1')
        parser.add_argument('-Q', '--queues', default=self.name)
        parser.add_argument('--prefetch-multiplier', default='1')
        parser.add_argument('--basic-auth', default='{}:{}'.format(self.name, self.config.get('MONITOR_PASSWORD')))
        args, unknownargs = parser.parse_known_args()
        if args.mode == 'route':
            print(self.url_map)
        elif args.mode == 'api':
            host = os.environ.get('HOST') or '0.0.0.0'
            port = int(os.environ.get('PORT') or '5000')
            single_thread = True if os.environ.get('SINGLE_THREAD') else False
            super().run(host=host, threaded=(not single_thread), port=port, debug=debug, **options)
        elif args.mode == 'worker':
            with self.app_context():
                self.celery.start(argv=['celery', 'worker', '-l', 'info', '-c', args.concurreny,
                                        '-Q', args.queues, '--prefetch-multiplier', args.prefetch_multiplier,
                                        '--pool', args.pool] + unknownargs)
        elif args.mode == 'beat':
            with self.app_context():
                self.celery.start(argv=['celery', 'beat'] + unknownargs)
        elif args.mode == 'monitor':
            with self.app_context():
                self.celery.start(argv=['celery', 'flower', '--basic-auth=' + args.basic_auth])
        else:
            print('Invalid Usage..')

    def _overwrite_res(self, sources, patches, is_module=False):
        name_cls = {}
        if is_module:
            list(map(lambda item: name_cls.update({item.__name__.split('.')[-1]: item}), sources))
            list(map(lambda item: name_cls.update({item.__name__.split('.')[-1]: item}), patches))
            return list(name_cls.values())
        else:
            list(map(lambda item: name_cls.update({item[0]: item[1]}), sources))
            list(map(lambda item: name_cls.update({item[0]: item[1]}), patches))
            return list(name_cls.items())

    def load_views(self, path):
        """
        load all view
        """
        # Load native views
        all_view_modules = list(import_submodules(bello_adam.views).values())
        if os.path.exists(path):
            package_name = path.replace('/', '.')
            package = importlib.import_module(package_name)
            customize_view_modules = import_submodules(package)
            all_view_modules = all_view_modules + list(customize_view_modules.values())

        for module in all_view_modules:
            lookup_view = lambda x: inspect.isclass(x) and x != ResourceView and not getattr(x, "_meta", {}).get(
                'abstract') and issubclass(x, ResourceView)
            lookup_bp = lambda x: isinstance(x, bello_adam.blueprint.Blueprint)
            views = inspect.getmembers(module, lookup_view)

            # filter, get rid of alias,
            # import bello_adam.views.user as BaseUser
            views = list(filter(lambda x: x[0] == x[1].__name__, views))
            if not views:
                raise SystemError('Missing View ' + module.__name__)
            name = views[0][0]
            resource = name
            cls_view = views[0][1]
            acl = cls_view.acl
            routes = {}
            bp = inspect.getmembers(module, lookup_bp)
            if bp:
                routes = bp[0][1].routes

            # check alias
            cls_parent = cls_view.__bases__[0]
            meta = getattr(cls_parent, "_meta", {})
            if cls_parent != ResourceView and not meta.get('abstract'):
                resource = cls_parent.__name__
                acl = cls_parent.acl + cls_view.acl
                bp = inspect.getmembers(sys.modules[cls_parent.__module__], lookup_bp)
                if bp:
                    # {'item': {}, 'collection': {}, 'remote_item': {}}
                    routes = {
                        'item': {**routes['item'], **bp[0][1].routes['item']},
                        'collection': {**routes['collection'], **bp[0][1].routes['collection']},
                        'remote_item': {**routes['remote_item'], **bp[0][1].routes['remote_item']}
                    }

            model = self.models.get(resource)
            view = cls_view(app=self, model=model, routes=routes)
            cls_view.acl = acl
            self.views[resource] = view

        for name, view in self.views.items():
            logger.debug('Loading View: %s', name)
            self.register_view(name, view, view.routes)

    def load_models(self, path):
        """
        load all mode logic
        """
        # Load System Models
        all_models_modules = list(import_submodules(bello_adam.models).values())

        if os.path.exists(path):
            package_name = path.replace('/', '.')
            package = importlib.import_module(package_name)
            customize_model_modules = import_submodules(package)
            all_models_modules = all_models_modules + list(customize_model_modules.values())

        for module in all_models_modules:
            lookup_model = lambda x: inspect.isclass(x) and x != ResourceDocument and issubclass(x, ResourceDocument)
            models = inspect.getmembers(module, lookup_model)
            # filter, get rid of alias,
            # import bello_adam.views.user as BaseUser
            models = list(filter(lambda x: x[0] == x[1].__name__, models))
            if not models:
                continue
                raise SystemError('Missing Model ' + module.__name__)
            name = models[-1][0]
            resource = name
            cls_model = models[-1][1]
            # check alias
            if cls_model.__bases__ and cls_model.__bases__[0] != ResourceDocument:
                new_resource = cls_model.__bases__[0].__name__
                self.models[new_resource] = cls_model
            self.models[resource] = cls_model

    def load_graph_models(self, path):
        """
        load all mode logic
        """
        # Load System Models
        all_graphs = discovery_items_in_package(bello_adam.models,
                                                lambda x: inspect.isclass(x) and x != GraphDocument and issubclass(x,
                                                                                                                   GraphDocument))

        if os.path.exists(path):
            package_name = path.replace('/', '.')
            package = importlib.import_module(package_name)
            customize_graphs = discovery_items_in_package(package, lambda x: inspect.isclass(
                x) and x != GraphDocument and issubclass(x, GraphDocument))
            all_graphs = all_graphs + customize_graphs

        for name, model in all_graphs:
            logger.debug('Load graph model %s', name)
            self.models[name] = model

    def load_middleware(self, path):
        """
        load all services
        """
        # Load System Services
        all_middlewares = discovery_items_in_package(bello_adam.middlewares,
                                                     lambda x: inspect.isclass(x) and x != Middleware and issubclass(x,
                                                                                                                     Middleware))

        if os.path.exists(path):
            package_name = path.replace('/', '.')
            package = importlib.import_module(package_name)
            customize_middlewares = discovery_items_in_package(package, lambda x: inspect.isclass(
                x) and x != Middleware and issubclass(x, Middleware))
            all_middlewares = all_middlewares + customize_middlewares

        for _k, _m in all_middlewares:
            logger.debug('Load middleware: %s', _k)
            self.middlewares[_k] = _m

    def load_service(self, path):
        """
        load all services
        """
        # Load System Services
        all_services = discovery_items_in_package(bello_adam.services,
                                                  lambda x: inspect.isclass(x) and x != Service and issubclass(x,
                                                                                                               Service))

        if os.path.exists(path):
            package_name = path.replace('/', '.')
            package = importlib.import_module(package_name)
            customize_services = discovery_items_in_package(package, lambda x: inspect.isclass(
                x) and x != Service and issubclass(x, Service))
            all_services = all_services + customize_services

        for _k, _m in all_services:
            name = _k.lower()
            _index = name.rindex('service')
            service_name = name[:_index] + '_' + name[_index:]
            service = _m(self)
            self.__setattr__(service_name, service)
            logger.debug('Load service: %s', service_name)
            self.services[service_name] = service

    def load_config(self):
        """ API settings are loaded from standard python modules. First from
        `settings.py`(or alternative name/path passed as an argument) and
        then, when defined, from the file specified in the
        `EVE_SETTINGS` environment variable.

        Since we are a Flask subclass, any configuration value supported by
        Flask itself is available (besides Adam's proper settings).

        .. versionchanged:: 0.6
           SchemaErrors raised during configuration
        .. versionchanged:: 0.5
           Allow EVE_SETTINGS envvar to be used exclusively. Closes #461.

        .. versionchanged:: 0.2
           Allow use of a dict object as settings.
        """

        # load defaults
        self.config.from_object('bello_adam.default_settings')

        # overwrite the defaults with custom user settings
        if isinstance(self.settings, dict):
            self.config.update(self.settings)
        else:
            if os.path.isabs(self.settings):
                pyfile = self.settings
            else:
                def find_settings_file(file_name):
                    # check if we can locate the file from sys.argv[0]
                    abspath = os.path.abspath(os.path.dirname(sys.argv[0]))
                    settings_file = os.path.join(abspath, file_name)
                    if os.path.isfile(settings_file):
                        return settings_file
                    else:
                        # try to find settings.py in one of the
                        # paths in sys.path
                        for p in sys.path:
                            for root, dirs, files in os.walk(p):
                                for f in fnmatch.filter(files, file_name):
                                    if os.path.isfile(os.path.join(root, f)):
                                        return os.path.join(root, file_name)

                # try to load file from environment variable or settings.py
                pyfile = find_settings_file(
                    os.environ.get('EVE_SETTINGS') or self.settings
                )

            if not pyfile:
                raise IOError('Could not load settings.')

            try:
                self.config.from_pyfile(pyfile)
            except:
                raise

        # flask-pymongo compatibility
        self.config['MONGO_CONNECT'] = self.config['MONGO_OPTIONS'].get(
            'connect', True
        )

    @property
    def api_prefix(self):
        """ Prefix to API endpoints.

        .. versionadded:: 0.2
        """
        return api_prefix(self.config['URL_PREFIX'],
                          self.config['API_VERSION'])

    def _add_url_rule(self, action_url, endpoint, view_func, methods):
        if 'OPTIONS' not in methods:
            methods = methods + ['OPTIONS']
        return self.add_url_rule(action_url, endpoint, view_func=view_func, methods=methods)

    def _add_resource_url_rules(self, name, view, routes=None):
        """ Builds the API url map for one resource. Methods are enabled for
        each mapped endpoint, as configured in the settings.

        .. versionchanged:: 0.5
           Don't add resource to url rules if it's flagged as internal.
           Strip regexes out of config.URLS helper. Closes #466.

        .. versionadded:: 0.2
        """
        name = underscore(name)
        view.__name__ = name
        url = '%s/%s' % (self.api_prefix, name)

        item_id_format = 'regex("[^/]{1,24}")'

        if view.meta['datasource'] == 'rest':
            logger.debug('load route for rest view %s', name)
            # collection query
            query_endpoint = 'proxy|proxy_collection_query|' + name + '|'
            self._add_url_rule(url + '/query', query_endpoint, view_func=view, methods=['GET'])

            for action, method in view.methods.items():
                endpoint = 'proxy|proxy_' + action + '|' + name + '|'
                rest_collection_url = url
                rest_item_url = '%s/<%s:%s>' % (rest_collection_url, item_id_format, 'id')
                if 'collection' in action:
                    action_url = rest_collection_url
                    if method.get('url'):
                        action_url = action_url + '/' + method['url']
                    self._add_url_rule(action_url, endpoint, view_func=view, methods=method['methods'])

                elif 'item' in action:
                    action_url = rest_item_url
                    if method.get('url'):
                        action_url = action_url + '/' + method['url']
                    self._add_url_rule(action_url, endpoint, view_func=view, methods=method['methods'])

        elif view.model and issubclass(view.model, ResourceDocument):
            logger.debug('load route for resource view %s', name)
            model = view.model
            for action, method in view.methods.items():
                endpoint = '|' + action + '|' + name + '|'
                action_url = '%s/<%s:%s>' % (url, item_id_format, 'id')
                if 'collection' in action:
                    action_url = url
                    if method.get('url'):
                        action_url = action_url + '/' + method['url']
                    self._add_url_rule(action_url, endpoint, view_func=view, methods=method['methods'])
                elif 'item' in action:
                    if method.get('url'):
                        action_url = action_url + '/' + method['url']
                    self._add_url_rule(action_url, endpoint, view_func=view, methods=method['methods'])
                elif 'batch' in action:
                    action_url = url + '/batch'
                    self._add_url_rule(action_url, endpoint, view_func=view, methods=method['methods'])

            if view.model._meta.get('index'):
                for action, method in view.query_methods.items():
                    if 'collection' in action:
                        action_url = '%s/%s/%s' % (self.api_prefix, name, method['url'])
                    elif 'item' in action:
                        action_url = '%s/<%s:%s>/%s' % (url, item_id_format, 'id', method['url'])
                    endpoint = '|' + action + '|' + name + '|'
                    self._add_url_rule(action_url, endpoint, view_func=view, methods=method['methods'])

            for field_name, field in view.model._fields.items():
                if isinstance(field, ReferenceField) or isinstance(field, LazyReferenceField):
                    reference = field.name
                    for action, method in view.reference_methods.items():
                        endpoint = '|' + action + '|' + name + '|' + field_name
                        reference_action_url = '%s/<%s:%s>/%s' % (url, item_id_format, 'id', reference)
                        if method.get('url'):
                            reference_action_url = reference_action_url + '/' + method['url']
                        self._add_url_rule(reference_action_url, endpoint, view_func=view, methods=method['methods'])
                    try:
                        document_type = field.document_type
                        for _, sub_field in document_type._fields.items():
                            if isinstance(sub_field, RemoteFileField):
                                media = sub_field.name.lower()
                                endpoint = '|item_reference_file' + '|' + name + '|' + media
                                media_action_url = '%s/<%s:%s>/<%s:%s>/<%s:%s>' % (
                                    url, item_id_format, 'id', item_id_format, 'field', item_id_format, 'sub_field')
                                self._add_url_rule(media_action_url, endpoint, view_func=view, methods=['GET'])
                    except Exception as ex:
                        pass
                if isinstance(field, ListField) and isinstance(field.field, EmbeddedDocumentField):
                    embedded = field.name
                    for action, method in view.embedded_methods.items():
                        endpoint = '|' + action + '|' + name + '|' + field_name
                        params = method.get('params') or {}
                        embedded_action_url = '%s/<%s:%s>/%s' % (url, item_id_format, 'id', embedded)
                        if params:
                            core_action_urls = []
                            for pn, pf in params.items():
                                core_action_urls.append('<%s:%s>' % (pf, pn))
                            action_url = url + '/'.join(core_action_urls)
                            embedded_action_url = embedded_action_url + "/" + action_url
                        self._add_url_rule(embedded_action_url, endpoint, view_func=view, methods=method['methods'])
                elif isinstance(field, RelationField):
                    relation = field.name
                    for action, method in view.relation_methods.items():
                        endpoint = '|' + action + '|' + name + '|' + field_name
                        relation_action_url = '%s/<%s:%s>/%s' % (url, item_id_format, 'id', relation)
                        if method.get('url'):
                            relation_action_url = relation_action_url + '/' + method['url']
                        self._add_url_rule(relation_action_url, endpoint, view_func=view, methods=method['methods'])
                elif isinstance(field, RemoteFileField):
                    # item_file
                    media = field.name.lower()
                    endpoint = '|item_file' + '|' + name + '|' + media
                    media_action_url = '%s/<%s:%s>/%s' % (url, item_id_format, 'id', media)
                    self._add_url_rule(media_action_url, endpoint, view_func=view, methods=['GET'])
                    # item_file_preview
                    media = field.name.lower()
                    endpoint = '|item_file_preview' + '|' + name + '|' + media
                    media_action_url = '%s/<%s:%s>/%s/preview' % (url, item_id_format, 'id', media)
                    self._add_url_rule(media_action_url, endpoint, view_func=view, methods=['GET'])
        elif view.model and issubclass(view.model, GraphDocument):
            # graph doc
            logger.debug('load route for graph view %s', name)
            for action, method in view.graph_methods.items():
                endpoint = '|' + action + '|' + name + '|'
                action_url = '%s/<%s:%s>' % (url, item_id_format, 'id')
                if 'collection' in action:
                    action_url = url
                    if method.get('url'):
                        action_url = action_url + '/' + method['url']
                    self._add_url_rule(action_url, endpoint, view_func=view, methods=method['methods'])
                elif 'item' in action:
                    if method.get('url'):
                        action_url = action_url + '/' + method['url']
                    self._add_url_rule(action_url, endpoint, view_func=view, methods=method['methods'])

        # bp endpoint
        if routes:
            datasource = 'proxy' if view.meta['datasource'] == 'rest' else ''

            for action, route in routes['item'].items():
                action_url = '%s/<%s:%s>/%s' % (url, item_id_format, 'id', action)
                endpoint = datasource + '|item@' + action + '|' + name + '|'
                self._add_url_rule(action_url, endpoint, view_func=view, methods=route['methods'])
            for action, route in routes['collection'].items():
                url = '%s/%s/%s' % (self.api_prefix, name, action)
                endpoint = datasource + '|collection@' + action + '|' + name + '|'
                self._add_url_rule(url, endpoint, view_func=view, methods=route['methods'])
            for action, route in routes['remote_item'].items():
                url = '%s/%s/' % (self.api_prefix, name)
                core_action_urls = []
                for pn, pf in route['params'].items():
                    core_action_urls.append('<%s:%s>' % (pf, pn))
                action_url = url + '/'.join(core_action_urls)
                endpoint = datasource + '|remote_item@' + action + '|' + name + '|'
                self._add_url_rule(action_url, endpoint, view_func=view, methods=route['methods'])

    def register_view(self, name, view, routes):
        self._add_resource_url_rules(name, view, routes)

    def unregister_view(self, name, view):
        """ 
        [危险操作] 直接操作flask的路由内部对象,来移除路由信息
        """
        name = underscore(name)
        for key in list(self.view_functions.keys()):
            if '|' in key:
                _, _, doc_name, _ = key.split('|')
                if doc_name == name:
                    del self.view_functions[key]
        item_to_delete = []
        for rule in self.url_map._rules:
            if '|' in rule.endpoint:
                _, _, doc_name, _ = rule.endpoint.split('|')
                if doc_name == name:
                    item_to_delete.append(rule)
                    del self.url_map._rules_by_endpoint[rule.endpoint]
        for item in item_to_delete:
            self.url_map._rules.remove(item)

    def __call__(self, environ, start_response):
        """ If HTTP_X_METHOD_OVERRIDE is included with the request and method
        override is allowed, make sure the override method is returned to Eve
        as the request method, so normal routing and method validation can be
        performed.
        """
        if self.config['ALLOW_OVERRIDE_HTTP_METHOD']:
            environ['REQUEST_METHOD'] = environ.get(
                'HTTP_X_HTTP_METHOD_OVERRIDE',
                environ['REQUEST_METHOD']).upper()
        return super().__call__(environ, start_response)
