# -*- coding:utf-8 -*-

import json
import time
import queue
import logging
import threading

from flask import Response, stream_with_context

from .json_util import CustomJSONEncoder


LOGGER = logging.getLogger(__name__)


class SseResponse:
    """
    sse响应类
    """
    def __init__(self, message_event_name='on_message', end_event_name='on_close', timeout=None):
        """
        初始化sse响应类
        :param message_event_name: sse消息事件名称(需要与前端约定)
        :param end_event_name: sse结束事件名称(需要与前端约定)
        :param timeout: 超时时间（秒），None表示永不超时
        """
        self.message_event_name = message_event_name
        self.end_event_name = end_event_name
        self.index = 0
        self.start_time = time.time()
        self.timeout = timeout

    def is_timeout(self):
        """
        检查是否超时
        :return: bool
        """
        if self.timeout is None:
            return False
        return time.time() - self.start_time > self.timeout

    def send(self, data, event_name=None):
        """发送SSE数据到前端
        :param data: sse数据
        :param event_name: 事件名称
        :return: sse响应的字符串
        """
        if self.is_timeout():
            return self.end({"type": self.end_event_name, "message": "Connection timeout"})

        self.index += 1
        if isinstance(data, (tuple, set)):
            data = list(data)
        if isinstance(data, (dict, list)):
            data = json.dumps(data, ensure_ascii=False, cls=CustomJSONEncoder)
        event_name = event_name or self.message_event_name
        sse_data = f'id: {self.index}\nevent: {event_name}\ndata: {data}\n\n'
        return sse_data

    def heart_beat(self):
        """发送SSE心跳事件到前端(必须定期发送，否则会被断开连接，然后重新请求)
        :return: sse结束响应的字符串
        """
        return self.send({"type": "heartbeat"})


    def end(self, data=None):
        """发送SSE结束事件到前端
        :return: sse结束响应的字符串
        """
        data = data or {"type": "end"}
        return self.send(data=data, event_name=self.end_event_name)


def sse_response_generator(fun, *args, **kwargs):
    """由于 真实运行的 函数会出现长时间阻塞，导致 SSE 重新请求。因此，使用线程池来实现异步处理。长时间没返回则发送心跳包。
    :param fun: 真实运行的函数
    :param args: 真实运行的函数参数
    :param kwargs: 真实运行的函数关键字参数
    :return: sse响应
    """
    output_queue = queue.Queue()
    sse = SseResponse()
    gen_thread = threading.Thread(target=generator_function, args=(fun, output_queue, sse, *args), kwargs=kwargs)
    gen_thread.start()  # 启动生成器线程

    while True:
        try:
            value = output_queue.get(timeout=5)  # 从队列中获取值，设置超时时间
            if value is None:  # 结束信号
                break
            yield value  # 输出值
        except queue.Empty:
            yield sse.heart_beat()  # 长时间没返回则发送心跳包


def generator_function(fun, output_queue, sse, *args, **kwargs):
    from adam.flask_app import current_app as app
    with app.app_context():
        for value in fun(sse, *args, **kwargs):
            output_queue.put(value)  # 将生成的值放入队列
        output_queue.put(None)  # 发送结束信号


def sse_stream(fun):
    """
    sse响应装饰器
    :param fun: 真实运行的函数
    :return: sse响应
    """
    return Response(
        stream_with_context(fun),
        # mimetype='text/event-stream',
        content_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )
