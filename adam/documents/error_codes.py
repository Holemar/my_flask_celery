# -*- coding:utf-8 -*-

import logging
from .exceptions import CodeType

logger = logging.getLogger(__name__)


class BaseError(object, metaclass=CodeType):

    crawl_error = (399, '爬虫获取网页信息异常！')

    unknown_error = (400, '未知错误！')
    unauthorized = (401, '未授权')
    forbidden = (402, '无权限')
    data_not_exist = (404, '数据不存在')
    handle_error = (405, 'view处理异常')
    method_not_allowed = (406, '不支持的请求方法')
    request_timeout = (408, '请求超时')

    system_error = (500, '服务器开小差了，请稍后重试~')  # 系统错误
    param_miss = (501, '参数缺失！')
    param_error = (502, '参数错误！')
    over_flow = (503, '超出访问次数限制！')
    over_limit = (504, '访问频次太高，请稍后重试！')
    license_expired = (505, '访问权限已到期，请续费！')

    no_user = (601, '用户未登录！')
    no_project = (602, '获取不到该用户的Project！')
    user_deleted = (603, '该用户已经被删除！')
    project_duplicate = (604, '该项目已经存在！')
