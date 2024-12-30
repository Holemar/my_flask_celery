
# run server
    Use Python 3.8 or above
    本项目实际开发环境: python3.11

| 功能               | 命令                             |
|------------------|--------------------------------|
| 启动 api 普通模式      | python3 main.py -m api     |
| 启动 api 正式发布模式    | python3 main.py -m web     |
| 启动 websocket    | python3 overseas.py -m websocket  |
| 启动 celery beat   | python3 main.py -m beat    |
| 启动 celery worker | python3 main.py -m worker  |
| 查看 api 接口        | python3 main.py -m route   |
| 进入交互模式           | python3 main.py -m shell   |
| 查看 celery 管理后台   | python3 main.py -m monitor |


# 项目说明
- 本项目为使用AI为企业提供咨询类服务。
- 使用 flask 作为 web 框架
- 使用 celery 管理任务
- 使用 mongoDb 作为数据库

# 安装依赖的第三方库
```sh
pip install -r requirements.txt
```


# api 开发说明
- 前端 html 及 js 代码，打包发布在 `static` 目录下
- 支持指定 URL 的接口，以及依赖 model 自动生成的接口

## 查看状况
- status 接口可以查看 celery 任务消耗情况。也可以查看 url、models、配置信息等
- 不加参数，只查看 celery 状况： http://{host}:{port}/api/status
- 通过参数控制，可以查看 url、models、配置信息等： http://{host}:{port}/api/status?url=1&models=1&beat=1
  1. `url=1` / `route=1`  查看所有的 api 路由
  2. `models=1` 查看所有的数据库 model
  3. `beat=1` 查看所有的定时任务配置


# celery 任务开发说明
- 支持定时任务和异步任务
- 异步任务/定时任务，写到目录 `apps/tasks` 下，会加载到 celery 任务队列中
- 抽离了定时任务的配置，写到异步任务所在的文件中，定义 SCHEDULE 变量中即可自动加载
- 支持继承 Task 的任务，也支持 celery.task 装饰器的任务
- 定义 BaseTask 基类，作为所有 celery.task 装饰器的任务的 base，可修改任务执行前后的多个事件
- 异步任务默认有3次异常重试机制，可在任务中设置重试次数
- 继承 BaseTask 基类的异步任务，提供了直接异步调用及同步调用两种静态方式


# 代码结构
```markdown
adam/  
├── adam/                                   # 主源代码目录  
│   ├── auth/                               # flask 认证模块，接口访问前的处理  
│   │   ├── token_backend.py                # Token 认证  
│   │   ├── basic_backend.py                # 基础认证  
│   │   └── __init__.py                     # 模块初始化文件  
│   │   
│   ├── documents/                          # 数据库模型基类  
│   │   ├── base.py                         # 基础数据库模型接口类   
│   │   ├── resource_document.py            # 基础数据库模型实现  
│   │   └── __init__.py                     # 模块初始化文件  
│   │  
│   ├── exceptions/                         # 异常定义  
│   │   ├── error_codes.py                  # 错误码定义  
│   │   ├── exceptions.py                   # 异常类定义  
│   │   └── __init__.py                     # 模块初始化文件  
│   │  
│   ├── fields/                             # 数据库模型字段定义  
│   │   ├── enum_field.py                   # 枚举字段  
│   │   ├── password_field.py               # 密码字段  
│   │   ├── relation_field.py               # 关系字段  
│   │   ├── ttl_field.py                    # TTL字段  
│   │   └── __init__.py                     # 模块初始化文件  
│   │  
│   ├── middlewares/                        # flask 中间件  
│   │   ├── base.py                         # 基础中间件  
│   │   ├── cors_middleware.py              # CORS中间件  
│   │   ├── license_limit_middleware.py     # 许可证限制中间件  
│   │   ├── token_middleware.py             # Token中间件  
│   │   └── __init__.py                     # 模块初始化文件  
│   │   
│   ├── models/                             # 公用数据库模型定义  
│   │   ├── cache_model.py                  # 缓存模型  
│   │   ├── common.py                       # 通用模型  
│   │   ├── log.py                          # 错误日志模型  
│   │   ├── log_api.py                      # API日志模型  
│   │   ├── work_status.py                  # celery 工作状态模型  
│   │   └── __init__.py                     # 模块初始化文件  
│   │  
│   ├── utils/                              # 工具函数库  
│   │   ├── bson_util.py                    # BSON工具  
│   │   ├── celery_util.py                  # Celery工具  
│   │   ├── config_util.py                  # 配置工具  
│   │   ├── db_util.py                      # 数据库工具  
│   │   ├── email_util.py                   # 邮件工具  
│   │   ├── es_model_util.py                # ES模型工具  
│   │   ├── es_util.py                      # ES工具  
│   │   ├── html_util.py                    # HTML工具  
│   │   ├── http_util.py                    # HTTP工具  
│   │   ├── import_util.py                  # 导入工具  
│   │   ├── json_util.py                    # JSON工具  
│   │   ├── log_filter.py                   # 日志过滤器  
│   │   ├── rc4.py                          # RC4加密  
│   │   ├── serializer.py                   # 序列化工具  
│   │   ├── str_util.py                     # 字符串工具  
│   │   ├── thread_util.py                  # 线程工具  
│   │   ├── time_util.py                    # 时间工具  
│   │   ├── url_util.py                     # URL工具  
│   │   └── __init__.py                     # 模块初始化文件  
│   │  
│   ├── views/                              # 视图基类  
│   │   ├── base.py                         # 视图基类，提供统一的增删改查接口及返回格式    
│   │   ├── blueprint.py                    # 类似于 flask blueprint，提供模块化的视图。但这个配合 base 视图使用    
│   │   ├── index.py                        # 定义前端入口视图、状态视图、错误视图    
│   │   └── __init__.py                     # 模块初始化文件  
│   │  
│   ├── celery_base_task.py                 # celery 任务基类  
│   ├── default_settings.py                 # 默认配置  
│   ├── flask_app.py                        # flask 的扩展，用于启动 Flask 应用  
│   └── __init__.py                         # 模块初始化文件  
│  
├── examples/                               # 范例代码  
│   ├── bs4_use.py                          # bs4 使用示例  
│   ├── model.py                            # 数据库模型示例  
│   ├── task.py                             # 定时任务示例  
│   ├── view.py                             # 视图示例  
│   └── __init__.py                         # 模块初始化文件  
│  
├── tests/                                  # 测试用例  
├── main.py                                 # 启动文件范例  
├── .gitignore                              # Git忽略配置  
├── readme.md                               # 说明文档  
├── settings.py                             # 配置文件范例  
└── requirements.txt                        # 主要依赖文件  
```
