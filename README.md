
# run server
    Use Python 3.8 or above
    本项目实际开发环境: python3.11

- run_api: python3 main.py -m api
- run_beat: python3 main.py -m beat
- run_worker: python3 main.py -m worker

## 项目说明
- 本项目仅用于 flask + celery 的练手，没有实际逻辑，便于阅读
- 支持定时任务和异步任务
- 抽离了定时任务的配置，到文件 `tasks/schedule.json`
- 异步任务/定时任务，写到目录 `tasks` 下，会加载到 celery 任务队列中
- 支持继承 Task 的任务，也支持 celery.task 装饰器的任务
- 定义 BaseTask 基类，作为所有 celery.task 装饰器的任务的 base，可修改任务执行前后的多个事件


## 环境变量

    BROKER_URL 是celery的代理人的地址,可以是 RabbitMQ、redis、mongodb等等
    CELERY_RESULT_BACKEND 是celery的运行结果存储地址,可以是 RabbitMQ、redis、mongodb等等

## 安装依赖的第三方库
```sh
pip install -r requirements.txt
```

