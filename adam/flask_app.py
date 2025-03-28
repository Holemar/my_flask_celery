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
import ctypes
import logging
import importlib
import inspect
import argparse
import multiprocessing

import celery
from flask import Flask
from mongoengine import register_connection
from mongoengine.fields import ListField, ReferenceField, LazyReferenceField, EmbeddedDocumentField

from .utils import celery_util, config_util
from .utils.import_util import import_submodules, load_modules, import_string
from .utils.url_util import RegexConverter, underscore
from .utils.log_filter import WerkzeugLogFilter, add_file_handler
from .views import ResourceView, Blueprint
from .documents import ResourceDocument, register_connection as async_register_connection
from .fields import RelationField
from .middlewares import Middleware


logger = logging.getLogger(__name__)
current_app = None  # 当前应用的 flask 实例
socketio = None  # 当前应用的 SocketIO 实例

COUNTER = multiprocessing.Value(ctypes.c_int, 0)  # wsgi子进程计数器
LOCK = multiprocessing.Lock()


class Adam(Flask):
    #: Allowed methods for resource endpoints
    supported_resource_methods = ['GET', 'POST', 'DELETE']

    #: Allowed methods for item endpoints
    supported_item_methods = ['GET', 'PATCH', 'DELETE', 'PUT']

    def __init__(self, import_name=__package__, root='', settings='settings', task_path='tasks', model_path='models',
                 enable_celery=False, static_folder=None, template_folder='templates', view_path='views',
                 url_converters=None, middleware_path='adam/middlewares', **kwargs):
        """  main WSGI app is implemented as a Flask subclass. Since we want
        to be able to launch our API by simply invoking Flask's run() method,
        we need to enhance our super-class a little bit.
        """
        global current_app, socketio
        logging.getLogger('werkzeug').addFilter(WerkzeugLogFilter())

        logger.info('Init Adam')
        cur_dir = os.path.dirname(__file__)
        self.current_file_dir = os.path.abspath(cur_dir)  # 当前文件所在目录
        self.root = root or os.getcwd()  # 项目启动目录

        if root:
            # 引入项目根目录以及lib跟目录
            sys.path.append(".")
            sys.path.append("./" + root)
            model_path = root + '/models'
            view_path = root + '/views'
            middleware_path = root + '/middlewares'

        kwargs['template_folder'] = template_folder
        static_folder = static_folder or os.path.join(os.getcwd(), 'static/')
        kwargs['static_folder'] = static_folder

        super().__init__(import_name, **kwargs)

        self.settings = settings
        self.view_path = view_path
        self.middleware_path = middleware_path
        self.load_config()

        # name
        self.name = self.config.get('APP_NAME') or 'default'

        # enable regex routing
        self.url_map.converters['regex'] = RegexConverter

        # optional url_converters and json encoder
        if url_converters:
            self.url_map.converters.update(url_converters)

        # Register mongoengine connections
        MONGO_CONNECTIONS = self.config.get('MONGO_CONNECTIONS', {})
        for k, v in MONGO_CONNECTIONS.items():
            register_connection(alias=k, host=v)  # 同步模式的 mongoengine 连接
            async_register_connection(k, v)  # 异步模式的 mongoengine 连接

        self.views = {}
        self.models = {}
        self.middlewares = {}

        # 加载model
        if MONGO_CONNECTIONS:
            self.load_models(model_path)

        # 加载celery(api端启动时也需要加载，让接口能抛出异步任务)
        if enable_celery:
            self.celery = celery.Celery(self.name)
            self.celery.config_from_object(self.config.get('CELERY_CONFIG'))
            celery_util.load_task(task_path, self.celery)  # 加载 tasks 目录下的任务
        else:
            self.celery = None

        if 'websocket' in sys.argv:
            # from gevent import monkey
            from flask_socketio import SocketIO
            # monkey.patch_all()  # socketio要想与flask通信必须打补丁。 交给外部统一处理(关键是提前处理)
            socketio = SocketIO(self, cors_allowed_origins=config_util.config.X_DOMAINS, async_mode='gevent',
                                message_queue=config_util.config.REDIS_URL)

        current_app = self

    def run(self, debug=None, **options):
        parser = argparse.ArgumentParser()
        parser.add_argument('-m', '--mode', choices=['route', 'api', 'web', 'websocket', 'worker', 'beat', 'monitor', 'shell'])
        parser.add_argument('--pool',
                            choices=['solo', 'gevent', 'prefork', 'eventlet', 'processes', 'threads', 'custom'],
                            default='solo')  # 并发模型，可选：prefork (默认，multiprocessing), eventlet, gevent, threads.
        parser.add_argument('-l', '--loglevel', default='INFO')  # 日志级别，可选：DEBUG, INFO, WARNING, ERROR, CRITICAL, FATAL
        parser.add_argument('-c', '--concurrency', default='')  # 并发数量，prefork 模型下就是子进程数量，默认等于 CPU 核心数
        ALL_QUEUES = self.config.get('ALL_QUEUES')
        if ALL_QUEUES:
            parser.add_argument('-Q', '--queues', default=','.join(ALL_QUEUES))
        parser.add_argument('--prefetch-multiplier', default='')
        parser.add_argument('-f', '--logfile', default='')
        parser.add_argument('-p', '--port', default='')
        parser.add_argument('-t', '--timeout', default='60')  # 超时时间，保持连接时间
        parser.add_argument('-w', '--workers', default=f'{multiprocessing.cpu_count()}')  # 启动的进程数
        parser.add_argument('-a', '--basic-auth', default='{}:{}'.format(self.config.get('MONITOR_USERNAME'), self.config.get('MONITOR_PASSWORD')))
        args, unknown_args = parser.parse_known_args()

        logfile = args.logfile or f'logs/{args.mode}.log'
        add_file_handler(logfile, args.loglevel)

        self.host = os.environ.get('HOST') or '0.0.0.0'
        self.port = int(os.environ.get('PORT') or '8000')
        if args.port:  # 端口号，优先级： 启动参数 -> 环境变量 -> 默认值
            self.port = int(args.port)
        if args.mode in ('route', 'api', 'websocket', 'web'):
            self.debug = debug
            self.load_route()  # 加载middleware、view
        celery_argv = ['celery'] if celery.__version__ < '5.2.0' else []

        if args.mode == 'route':
            print(self.url_map)
            print('views:', self.views)
            print('models:', self.models)
            print('middlewares:', self.middlewares)
        elif args.mode == 'api':
            single_thread = True if os.environ.get('SINGLE_THREAD') else False
            super().run(host=self.host, threaded=(not single_thread), port=self.port, debug=debug, **options)
        elif args.mode == 'websocket':  # 启动 websocket 服务器，效果跟 flask api 一样
            logger.info(f'Start websocket server  {self.host}:{self.port}')
            socketio.run(self, host=self.host, port=self.port)
        elif args.mode == 'web':  # 启动gunicorn服务器，也可以改成直接 gunicorn 启动
            import gunicorn
            from gunicorn.app.wsgiapp import run
            app_module = os.path.splitext(sys.argv[0])[0]
            prog = inspect.getfile(gunicorn)
            prog = prog.rstrip('__init__.py').rstrip(os.sep)
            # ugly: 通过修改 sys.argv 实现 gunicorn 启动参数的传递
            sys.argv = [prog, '-w', args.workers, '-b', f'{self.host}:{self.port}',
                        f'--timeout={args.timeout}', f'--graceful-timeout={args.timeout}', '--keep-alive=5']  # 超时时间
            if args.pool == 'gevent':
                sys.argv += ['-k', 'gevent']   # 启用 gevent 模型
            sys.argv += ['--log-level=' + args.loglevel.lower(), '--log-file=logs/web_error.log', f'{app_module}:app']
            run(prog="gunicorn")
        elif args.mode == 'worker':
            celery_argv += ['worker', '-l', args.loglevel, '--pool', args.pool, '-Q', args.queues]
            ''' 交给外部统一处理(关键是提前处理)
            if args.pool == 'gevent':
                from gevent import monkey
                monkey.patch_all()
            '''
            if args.concurrency:
                celery_argv += ['-c', args.concurrency]
            if args.prefetch_multiplier:
                celery_argv += ['--prefetch-multiplier', args.prefetch_multiplier]
            self.celery.start(argv=celery_argv + unknown_args)
        elif args.mode == 'beat':
            self.celery.start(argv=celery_argv + ['beat', '-l', args.loglevel] + unknown_args)
        elif args.mode == 'monitor':
            self.celery.start(argv=celery_argv + ['flower', '--basic-auth=' + args.basic_auth,
                                                  '--address=' + self.host, '--port=' + str(self.port)])
        elif args.mode == 'shell':
            from IPython import embed
            from .utils.serializer import mongo_to_dict
            app = self
            celery_app = self.celery
            with self.app_context():
                embed(header='Shell')
        else:
            print('Invalid Usage..')

    def init_wsgi_server(self):
        """
        程序运行在wsgi服务器上，需要执行的初始化操作(子进程启动时调用)
        """
        logger.info('Init wsgi server')
        self.load_route()  # 加载middleware、view

        ''' # 主进程已经写了日志文件，子进程就不用重复写了
        # 各子进程使用独立的日志文件，因为共用会导致日志内容混乱甚至丢失
        global COUNTER
        with LOCK:
            COUNTER.value += 1
            item = COUNTER.value

        log_file = f'logs/web{item}.log'
        parser = argparse.ArgumentParser()
        parser.add_argument('--log-level', default='INFO')  # 日志级别，可选：DEBUG, INFO, WARNING, ERROR, CRITICAL, FATAL
        args, unknown_args = parser.parse_known_args()
        add_file_handler(log_file, args.log_level.upper())
        logger.info('set log file: %s, level: %s', log_file, args.log_level)
        '''

    def load_route(self):
        # 加载view
        self.load_views(self.view_path)

        load_middlewares = [
            'TokenMiddleware',
            'CorsMiddleware'
        ]
        for oth_midd in self.config.get('MIDDLEWARS', []):
            if oth_midd not in load_middlewares:
                load_middlewares.append(oth_midd)
        self.available_middlewares = []
        self.load_middleware(self.middleware_path)

        # 加载自定义中间件
        for middleware in load_middlewares:
            if middleware in self.middlewares:
                self.available_middlewares.append(self.middlewares[middleware])
                logger.debug('Register middleware %s', middleware)
            else:
                logger.error('unregistered middleware %s', middleware)

        self.auth_backends = []
        for ab in self.config.get('AUTHENTICATION_BACKENDS') or ['adam.auth.token_backend']:
            auth_module = importlib.import_module(ab)
            is_class_member = lambda member: inspect.isclass(member) and member.__module__ == auth_module.__name__
            clsmembers = inspect.getmembers(auth_module, is_class_member)
            self.auth_backends.append(clsmembers[0][1]())

        with self.app_context():
            # 注册特殊页面(首页、静态文件、status、错误处理等)
            from .views import index
            try:
                importlib.reload(index)  # wsgi 服务器下，子进程会不再加载，导致少了这些接口
            except AssertionError:
                pass
        logger.info('load_route views: %s, urls: %s', len(self.views), len(list(self.url_map.iter_rules())))

    def load_views(self, path):
        """
        load all view
        """
        # Load native views
        all_view_modules = []
        try:
            package_name = path.replace('/', '.').replace(os.sep, '.')
            package = importlib.import_module(package_name)
            customize_view_modules = import_submodules(package)
            all_view_modules = list(customize_view_modules.values())
        except (ImportError, ModuleNotFoundError):
            pass

        lookup_view = lambda x: (inspect.isclass(x) and x != ResourceView
                                 and not getattr(x, "_meta", {}).get('abstract') and issubclass(x, ResourceView))
        lookup_bp = lambda x: isinstance(x, Blueprint)
        for module in all_view_modules:
            views = inspect.getmembers(module, lookup_view)

            # filter, get rid of alias,
            # import bello_adam.views.user as BaseUser
            views = list(filter(lambda x: x[0] == x[1].__name__, views))
            if not views:
                continue
            name = views[0][0]
            resource = name
            cls_view = views[0][1]
            acl = cls_view.acl.copy()
            routes = {}
            bp = inspect.getmembers(module, lookup_bp)
            bp_obj = bp[0][1] if bp else None
            if bp:
                routes.update(bp_obj.routes)
                acl.extend(bp_obj.acl)
                bp_name = bp_obj.name
                if bp_name and bp_name.startswith(package_name):
                    resource = bp_name[len(package_name) + 1:]

            # check alias
            cls_parent = cls_view.__bases__[0]
            meta = getattr(cls_parent, "_meta", {})
            if cls_parent != ResourceView and not meta.get('abstract'):
                resource = cls_parent.__name__
                acl = cls_parent.acl + cls_view.acl
                bp = inspect.getmembers(sys.modules[cls_parent.__module__], lookup_bp)
                if bp:
                    routes = {
                        'item': {**routes['item'], **bp_obj.routes['item']},
                        'collection': {**routes['collection'], **bp_obj.routes['collection']},
                        'remote_item': {**routes['remote_item'], **bp_obj.routes['remote_item']}
                    }

            model = self.models.get(resource) or self.models.get(name)
            view = cls_view(app=self, model=model, routes=routes)
            view.acl = acl
            self.views[resource] = view

        for name, view in self.views.items():
            logger.debug('Loading View: %s', name)
            self.register_view(name, view, view.routes)

    def load_models(self, path):
        """
        load all model logic
        """
        lookup_model = lambda x: inspect.isclass(x) and x != ResourceDocument and issubclass(x, ResourceDocument)
        self.models = load_modules('adam.models', lookup_model)
        self.models.update(load_modules(path, lookup_model))

    def load_middleware(self, path):
        """
        load all middleware
        """
        func_lookup = lambda x: inspect.isclass(x) and x != Middleware and issubclass(x, Middleware)
        self.middlewares = load_modules(path, func_lookup)

    def load_config(self):
        """ API settings are loaded from standard python modules. First from
        `settings.py`(or alternative name/path passed as an argument) and
        then, when defined, from the file specified in the
        `EVE_SETTINGS` environment variable.

        Since we are a Flask subclass, any configuration value supported by
        Flask itself is available (besides Adam's proper settings).
        """
        self.config.from_object('adam.default_settings')

        # overwrite the defaults with custom user settings
        if isinstance(self.settings, dict):
            self.config.update(self.settings)
        elif isinstance(self.settings, str):
            try:
                settings = import_string(self.settings)
                for key in dir(settings):
                    if not key.isupper():
                        continue
                    value = getattr(settings, key)
                    if isinstance(value, (int, float, str, bool, list, tuple)):
                        self.config[key] = value
                    elif isinstance(value, dict):
                        if key in self.config and isinstance(self.config[key], dict):
                            self.config[key].update(value)
                        else:
                            self.config[key] = value
                    # 是一个类，逐个属性填充
                    elif type(value).__name__ == 'type':
                        origin_object = self.config.get(key)
                        for k in dir(value):
                            if k.startswith('__'):
                                continue
                            setattr(origin_object, k, getattr(value, k))
            except ImportError:
                pass

        # flask-pymongo compatibility
        self.config['MONGO_CONNECT'] = self.config['MONGO_OPTIONS'].get('connect', True)
        config_util.config.add_values(self.config)

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

            if model._meta.get('index'):
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
