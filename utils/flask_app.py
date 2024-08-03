# -*- coding: utf-8 -*-
"""
    flask 启动文件
    ~~~~~~~~~~~~

    This module implements the central WSGI application object as a Flask
    subclass.

    :copyright: (c) 2024 by Holemar Feng<daillow@gmail.com>.
"""
import os
import sys
import fnmatch
import logging
import importlib
import inspect
import argparse

import click
import celery
from flask import Flask
from mongoengine import register_connection

from utils import celery_util
from utils.blueprint import Blueprint
from utils.import_util import import_submodules, discovery_items_in_package
from utils.url_util import RegexConverter, underscore
from utils.log_filter import WerkzeugLogFilter
from utils.view import ResourceView

from bello_adam import ResourceDocument, GraphDocument, Service, Middleware


logger = logging.getLogger(__name__)


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
            self.celery = celery.Celery(self.name)
            self.celery.config_from_object(self.config.get('CeleryConfig'))

            celery_util.load_task(task_path)  # 加载 tasks 目录下的任务
            celery_util.load_task_schedule(os.path.join(self.root, task_path, 'schedule.json'))  # 加载定时任务

        for k, s in self.services.items():
            logger.debug('service on_loaded trigger %s', k)
            s.on_loaded()

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
        parser.add_argument('-m', '--mode', choices=['worker', 'beat'])
        parser.add_argument('-p', '--pool', choices=['solo', 'gevent', 'prefork', 'eventlet'], default='solo')  # 并发模型，可选：prefork (默认，multiprocessing), eventlet, gevent, threads.
        parser.add_argument('-l', '--loglevel', default='INFO')  # 日志级别，可选：DEBUG, INFO, WARNING, ERROR, CRITICAL, FATAL
        parser.add_argument('-c', '--concurrency', default='')  # 并发数量，prefork 模型下就是子进程数量，默认等于 CPU 核心数
        parser.add_argument('-Q', '--queues', default=','.join(self.config.get('ALL_QUEUES')))
        parser.add_argument('--prefetch-multiplier', default='')
        parser.add_argument('--logfile', default='')
        parser.add_argument('--basic-auth', default='{}:{}'.format(self.config.get('MONITOR_USERNAME'), self.config.get('MONITOR_PASSWORD')))
        args, unknown_args = parser.parse_known_args()
        if args.logfile:
            # 没有日志文件的目录，则先创建目录，避免因此报错
            file_path = os.path.dirname(os.path.abspath(args.logfile))
            if not os.path.isdir(file_path):
                os.makedirs(file_path)

        celery_argv = ['celery'] if celery.__version__ < '5.2.0' else []
        if args.mode == 'route':
            print(self.url_map)
        elif args.mode == 'api':
            host = os.environ.get('HOST') or '0.0.0.0'
            port = int(os.environ.get('PORT') or '8000')
            single_thread = True if os.environ.get('SINGLE_THREAD') else False
            super().run(host=host, threaded=(not single_thread), port=port, debug=debug, **options)
        elif args.mode == 'worker':
            celery_argv += ['worker', '-l', args.loglevel, '--pool', args.pool, '-Q', args.queues]
            if args.concurrency:
                celery_argv += ['-c', args.concurrency]
            if args.prefetch_multiplier:
                celery_argv += ['--prefetch-multiplier', args.prefetch_multiplier]
            self.celery.start(argv=celery_argv + unknown_args)
        elif args.mode == 'beat':
            self.celery.start(argv=celery_argv + ['beat', '-l', args.loglevel] + unknown_args)
        elif args.mode == 'monitor':
            self.celery.start(argv=celery_argv + ['flower', '--basic-auth=' + args.basic_auth])
        else:
            print('Invalid Usage..')

    def load_views(self, path):
        """
        load all view
        """
        # Load native views
        all_view_modules = list()
        if os.path.exists(path):
            package_name = path.replace('/', '.')
            package = importlib.import_module(package_name)
            customize_view_modules = import_submodules(package)
            all_view_modules = all_view_modules + list(customize_view_modules.values())

        for module in all_view_modules:
            lookup_view = lambda x: inspect.isclass(x) and x != ResourceView and not getattr(x, "_meta", {}).get(
                'abstract') and issubclass(x, ResourceView)
            lookup_bp = lambda x: isinstance(x, Blueprint)
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
        all_models_modules = list()

        if os.path.exists(path):
            package_name = path.replace('/', '.')
            package = importlib.import_module(package_name)
            customize_model_modules = import_submodules(package)
            all_models_modules = all_models_modules + list(customize_model_modules.values())

        for module in all_models_modules:
            lookup_model = lambda x: inspect.isclass(x) and x != ResourceDocument and issubclass(x, ResourceDocument)
            models = inspect.getmembers(module, lookup_model)
            # filter, get rid of alias,
            models = list(filter(lambda x: x[0] == x[1].__name__, models))
            if not models:
                continue
            name = models[-1][0]
            resource = name
            cls_model = models[-1][1]
            # check alias
            if cls_model.__bases__ and cls_model.__bases__[0] != ResourceDocument:
                new_resource = cls_model.__bases__[0].__name__
                self.models[new_resource] = cls_model
            self.models[resource] = cls_model

    def load_middleware(self, path):
        """
        load all services
        """
        all_middlewares = []
        func_lookup = lambda x: inspect.isclass(x) and x != Middleware and issubclass(x, Middleware)

        if os.path.exists(path):
            package_name = path.replace('/', '.')
            package = importlib.import_module(package_name)
            customize_middlewares = discovery_items_in_package(package, func_lookup)
            all_middlewares = all_middlewares + customize_middlewares

        for _k, _m in all_middlewares:
            logger.debug('Load middleware: %s', _k)
            self.middlewares[_k] = _m

    def load_service(self, path):
        """
        load all services
        """
        all_services = []

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
        """
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
                pyfile = find_settings_file(os.environ.get('EVE_SETTINGS') or self.settings)

            if not pyfile:
                raise IOError('Could not load settings.')

            try:
                self.config.from_pyfile(pyfile)
            except:
                raise

        # flask-pymongo compatibility
        self.config['MONGO_CONNECT'] = self.config['MONGO_OPTIONS'].get('connect', True)

    @property
    def api_prefix(self):
        """ Prefix to API endpoints.
        """
        url_prefix = self.config.get('URL_PREFIX')
        api_version = self.config.get('API_VERSION')

        prefix = '/%s' % url_prefix if url_prefix else ''
        version = '/%s' % api_version if api_version else ''
        return prefix + version

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
        if self.config.get('ALLOW_OVERRIDE_HTTP_METHOD', True):
            environ['REQUEST_METHOD'] = environ.get('HTTP_X_HTTP_METHOD_OVERRIDE', environ.get('REQUEST_METHOD')).upper()
        return super().__call__(environ, start_response)
