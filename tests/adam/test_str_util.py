# -*- coding:utf-8 -*-
"""
string Utility unittest
"""

import unittest

from adam.utils import str_util


class TestStrUtil(unittest.TestCase):

    def test_str_bytes(self):
        a = "哈哈xyz呵呵馬大親"
        s = str_util.decode2str(a)
        self.assertEqual(a, s)
        self.assertTrue(isinstance(s, str))

        c = b'absde'
        s2 = str_util.decode2str(c)
        self.assertTrue(isinstance(s2, str))
        self.assertEqual('absde', s2)

        b = str_util.encode2bytes(a)
        self.assertTrue(isinstance(b, bytes))
        d = str_util.encode2bytes(c)
        self.assertTrue(isinstance(d, bytes))
        self.assertEqual(c, d)

    def test_to_utf8_str(self):
        a = "哈哈xyz呵呵馬大親"
        for code in ('utf-8', 'GBK', 'big5', 'GB18030', 'unicode-escape'):
            # bytes
            b = bytes(a, code)
            s = str_util.to_utf8_str(b)
            self.assertTrue(isinstance(s, str))
            self.assertEqual(s, a)
            # bytearray
            br = bytearray(a, code)
            s = str_util.to_utf8_str(br)
            self.assertTrue(isinstance(s, str))
            self.assertEqual(s, a)

    def test_to_utf8_bytes(self):
        # big5
        a = "馬xyz大親"
        b0 = bytes(a, 'utf-8')
        code = 'big5'
        s0 = b0.decode(code)
        b2 = str_util.to_utf8_bytes(s0)
        self.assertTrue(isinstance(b2, bytes))
        self.assertEqual(b2, b0)
        # str
        s = str_util.to_utf8_str(s0)
        self.assertTrue(isinstance(s, str))
        self.assertEqual(s, a)

        a = "哈哈xyz呵呵大的"
        b0 = bytes(a, 'utf-8')
        for code in ('utf-8', 'gbk', 'GB18030', 'unicode-escape'):
            s0 = b0.decode(code)
            b2 = str_util.to_utf8_bytes(s0)
            self.assertTrue(isinstance(b2, bytes))
            self.assertEqual(b2, b0)
            # str
            s = str_util.to_utf8_str(s0)
            self.assertTrue(isinstance(s, str))
            self.assertEqual(s, a)

    def test_base64(self):
        a = "W1tdLCB7fSwgeyJjYWxsYmFja3MiOiBudWxsLCAiZXJyYmFja3MiOiBudWxsLCAiY2hhaW4iOiBudWxsLCAiY2hvcmQiOiBudWxsfV0="
        ra = '[[], {}, {"callbacks": null, "errbacks": null, "chain": null, "chord": null}]'
        self.assertEqual(str_util.base64_decode(a), ra)
        self.assertEqual(str_util.base64_encode(ra), a)

    # gzip 压缩测试
    def test_gzip(self):
        value = {'a': [1, 2, '呵xx呵', u'哈"哈', '智汇云']}
        json_value = '{"a": [1, 2, "\\u5475xx\\u5475", "\\u54c8\\"\\u54c8", "\\u667a\\u6c47\\u4e91"]}'
        gzip_value = str_util.gzip_encode(value)
        value1 = str_util.gzip_decode(gzip_value)
        assert value1 == json_value  # 压缩之后会将 dict 转码成字符串
        assert len(gzip_value) < len(value1)

    # zlib 压缩测试
    def test_zlib(self):
        value = {'a': [1, 2, '呵xx呵', u'哈"哈', '智汇云']}
        json_value = '{"a": [1, 2, "\\u5475xx\\u5475", "\\u54c8\\"\\u54c8", "\\u667a\\u6c47\\u4e91"]}'
        zlib_value = str_util.zlib_encode(value)
        value2 = str_util.zlib_decode(zlib_value)
        assert value2 == json_value  # 压缩之后会将 dict 转码成字符串
        assert len(zlib_value) < len(value2)

    def test_is_phone(self):
        self.assertTrue(str_util.is_phone('13800138000'))
        self.assertFalse(str_util.is_phone('8613800138000'))
        self.assertFalse(str_util.is_phone('11800138000'))
        self.assertFalse(str_util.is_phone('138-00138-000'))

    def test_is_email(self):
        self.assertTrue(str_util.is_email('13800138000@QQ.com'))
        self.assertTrue(str_util.is_email('test123@gmail.com.cn'))
        self.assertFalse(str_util.is_email('13800138000#QQ.com'))
        self.assertFalse(str_util.is_email('av c.dd.dd-ff@qq.com-cn'))
        self.assertFalse(str_util.is_email('地址dd.dd-ff@qq.com-cn'))


if __name__ == "__main__":
    unittest.main()
