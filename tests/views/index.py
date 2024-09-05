# -*- coding:utf-8 -*-

import json
import unittest
import __init__  # 导入环境


class TestIndexView(unittest.TestCase):
    """测试 adam/views/index"""
    def test_empty_name_password(self):
        """测试模拟场景，用户名或密码不完整"""
        # 使用客户端向后端发送 get/post 请求, data指明发送的数据，会返回一个响应对象
        response = self.client.get("/status", data={})

        # respoonse.data是响应体数据
        resp_json = response.data
        print(resp_json)

        # 按照json解析
        resp_dict = json.loads(resp_json)

        # 使用断言进行验证：是否存在code字符串在字典中
        self.assertIn("beat", resp_dict)


if __name__ == '__main__':
    unittest.main()
