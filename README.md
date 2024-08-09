
# run server
    Use Python 3.8 or above
    本项目实际开发环境: python3.11

功能 | 命令
--- | ---
run_api | python3 main.py -m api
run_beat | python3 main.py -m beat
run_worker | python3 main.py -m worker
查看所有接口 | python3 main.py -m route


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

## 查看允许状况
- status 接口可以查看 celery 任务消耗情况。也可以查看 url、models、配置信息等
- 不加参数，只查看 celery 状况： http://127.0.0.1:8000/status
- 通过参数控制，可以查看 url、models、配置信息等： http://127.0.0.1:8000/status?url=1&models=1&config=1


# celery 任务开发说明
- 支持定时任务和异步任务
- 抽离了定时任务的配置，到文件 `tasks/schedule.json`
- 异步任务/定时任务，写到目录 `tasks` 下，会加载到 celery 任务队列中
- 支持继承 Task 的任务，也支持 celery.task 装饰器的任务
- 定义 BaseTask 基类，作为所有 celery.task 装饰器的任务的 base，可修改任务执行前后的多个事件

