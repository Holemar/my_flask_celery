#!python
# -*- coding:utf-8 -*-
"""
公用函数 rc4.py 的测试类
Created on 2014/7/16
Updated on 2019/1/18
@author: Holemar
"""
import sys
import time
import logging
import unittest

from adam.utils import rc4

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


class RC4Test(unittest.TestCase):

    def test_encode_decode(self):
        key = "1bb762f7ce24ceee"

        # 英文加密测试
        txt = 'abc321cc55+-*/,.,.dfdehryz908&^%$#@!~*()_+-='
        secret_txt = rc4.encode(txt, key)
        assert secret_txt
        assert rc4.decode(secret_txt, key) == txt

        # 中文加密测试
        txt = '哈哈5+-*/,.,.dfd08&^%$#@!~*()_+-='
        secret_txt = rc4.encode(txt, key)
        assert secret_txt
        assert rc4.decode(secret_txt, key) == txt

        check_unicode = True
        if PY2:
            try:
                # py2 的中文加密测试
                unicode
                txt = u'哈哈5+-*/,.,.dfd08&^%$#@!~*()_+-='
                check_unicode = False
                secret_txt = rc4.encode(txt, key)
                assert secret_txt
                assert rc4.decode(secret_txt, key) == txt.encode("utf-8")
                check_unicode = True
            except NameError:
                pass
        assert check_unicode

    def test_param(self):
        key = "1bb762f7ce24ceee"

        # 明文参数为空测试
        secret_txt = rc4.encode('', key)
        assert not secret_txt
        secret_txt = rc4.encode(None, key)
        assert not secret_txt

        # 密文参数为空测试
        real_text = rc4.decode('', key)
        assert not real_text
        real_text = rc4.decode(None, key)
        assert not real_text

        # 加密 key 为空测试
        txt = '13800138000'
        has_error = False
        try:
            secret_txt = rc4.encode(txt, '')
        except:
            has_error = True
        assert has_error

        has_error = False
        try:
            secret_txt = rc4.encode(txt, None)
        except:
            has_error = True
        assert has_error

        # 解密 key 为空测试
        has_error = False
        try:
            real_text = rc4.decode(txt, '')
        except:
            has_error = True
        assert has_error

        has_error = False
        try:
            real_text = rc4.decode(txt, None)
        except:
            has_error = True
        assert has_error

    def test_english_stress(self):
        # 纯英文+数字 性能 测试
        repeat_times = 100
        key = "1bb762f7ce24ceee"
        txt = '1525dsfsdijrwemrkwerw5484856er' * 10

        start_time = time.time()
        cipher = rc4.encode(txt, key)
        end_time = time.time()
        logging.info('*' * 100)
        logging.info(u'单次加密耗时：%.4f秒' % (end_time - start_time))

        start_time = time.time()
        for i in range(repeat_times):
            cipher = rc4.encode(txt, key)
        end_time = time.time()
        logging.info(u'%d次加密耗时：%.4f秒' % (repeat_times, end_time - start_time))

        start_time = time.time()
        decr = rc4.decode(cipher, key)
        end_time = time.time()
        logging.info(u'单次解密耗时：%.4f秒' % (end_time - start_time))

        start_time = time.time()
        for i in range(repeat_times):
            decr = rc4.decode(cipher, key)
        end_time = time.time()
        logging.info(u'%d次解密耗时：%.4f秒' % (repeat_times, end_time - start_time))
        logging.info('*' * 100)

    def test_chinese_stress(self):
        # 中文 性能 测试
        repeat_times = 100
        key = "1bb762f7ce24ceee"
        txt = '15呵呵5@#E$$@#gh，。h()_=154中文4*4616' * 10

        start_time = time.time()
        cipher = rc4.encode(txt, key)
        end_time = time.time()
        logging.info('*' * 100)
        logging.info(u'单次加密耗时：%.4f秒' % (end_time - start_time))

        start_time = time.time()
        for i in range(repeat_times):
            cipher = rc4.encode(txt, key)
        end_time = time.time()
        logging.info(u'%d次加密耗时：%.4f秒' % (repeat_times, end_time - start_time))

        start_time = time.time()
        decr = rc4.decode(cipher, key)
        end_time = time.time()
        logging.info(u'单次解密耗时：%.4f秒' % (end_time - start_time))

        start_time = time.time()
        for i in range(repeat_times):
            decr = rc4.decode(cipher, key)
        end_time = time.time()
        logging.info(u'%d次解密耗时：%.4f秒' % (repeat_times, end_time - start_time))
        logging.info('*' * 100)

    def test_symmetrical(self):
        key = "1bb762f7ce24ceee"

        # 英文加密测试
        txt = 'abc321cc55+-*/,.,.dfdehryz908&^%$#@!~*()_+-='
        secret_txt = rc4.encode_symmetrical(txt, key)
        assert secret_txt
        assert rc4.decode_symmetrical(secret_txt, key) == txt

        # 中文加密测试
        txt = '哈哈5+-*/,.,.dfd08&^%$#@!~*()_+-='
        secret_txt = rc4.encode_symmetrical(txt, key)
        assert secret_txt
        assert rc4.decode_symmetrical(secret_txt, key) == txt

        check_unicode = True
        if PY2:
            try:
                # py2 的中文加密测试
                unicode
                txt = u'哈哈5+-*/,.,.dfd08&^%$#@!~*()_+-='
                check_unicode = False
                secret_txt = rc4.encode_symmetrical(txt, key)
                assert secret_txt
                assert rc4.decode_symmetrical(secret_txt, key) == txt.encode("utf-8")
                check_unicode = True
            except NameError:
                pass
        assert check_unicode

        # 一一对应测试
        txt = '0呵呵1A051哈哈'
        txt2 = 'aAa...'
        v1 = rc4.encode_symmetrical(txt, key)
        v2 = rc4.encode_symmetrical(txt2, key)
        assert rc4.decode_symmetrical(v1, key) == txt
        assert rc4.decode_symmetrical(v2, key) == txt2
        assert rc4.encode_symmetrical(txt + txt2, key) == v1 + v2
        assert rc4.encode_symmetrical(txt2 + txt, key) == v2 + v1

    def test_symmetrical_param(self):
        key = "1bb762f7ce24ceee"

        # 明文参数为空测试
        secret_txt = rc4.encode_symmetrical('', key)
        assert not secret_txt
        secret_txt = rc4.encode_symmetrical(None, key)
        assert not secret_txt

        # 密文参数为空测试
        real_text = rc4.decode_symmetrical('', key)
        assert not real_text
        real_text = rc4.decode_symmetrical(None, key)
        assert not real_text

        # 加密 key 为空测试
        txt = '13800138000'
        has_error = False
        try:
            secret_txt = rc4.encode_symmetrical(txt, '')
        except:
            has_error = True
        assert has_error

        has_error = False
        try:
            secret_txt = rc4.encode_symmetrical(txt, None)
        except:
            has_error = True
        assert has_error

        # 解密 key 为空测试
        has_error = False
        try:
            real_text = rc4.decode_symmetrical(txt, '')
        except:
            has_error = True
        assert has_error

        has_error = False
        try:
            real_text = rc4.decode_symmetrical(txt, None)
        except:
            has_error = True
        assert has_error

    def test_english_symmetrical_stress(self):
        # 纯英文+数字 性能 测试
        repeat_times = 100
        key = "1bb762f7ce24ceee"
        txt = '1525dsfsdijrwemrkwerw5484856er'
        # txt = '1'*18

        start_time = time.time()
        cipher = rc4.encode_symmetrical(txt, key)
        end_time = time.time()
        logging.info('=' * 100)
        logging.info(u'单次加密耗时：%.4f秒' % (end_time - start_time))

        start_time = time.time()
        for i in range(repeat_times):
            cipher = rc4.encode_symmetrical(txt, key)
        end_time = time.time()
        logging.info(u'%d次加密耗时：%.4f秒' % (repeat_times, end_time - start_time))

        start_time = time.time()
        decr = rc4.decode_symmetrical(cipher, key)
        end_time = time.time()
        logging.info(u'单次解密耗时：%.4f秒' % (end_time - start_time))

        start_time = time.time()
        for i in range(repeat_times):
            decr = rc4.decode_symmetrical(cipher, key)
        end_time = time.time()
        logging.info(u'%d次解密耗时：%.4f秒' % (repeat_times, end_time - start_time))
        logging.info('=' * 100)

    def test_chinese_symmetrical_stress(self):
        # 中文 性能 测试
        repeat_times = 100
        key = "1bb762f7ce24ceee"
        txt = '15呵呵5@#E$$@#gh，。h()_=154中文4*4616'
        # txt = '1'*18

        start_time = time.time()
        cipher = rc4.encode_symmetrical(txt, key)
        end_time = time.time()
        logging.info('=' * 100)
        logging.info(u'单次加密耗时：%.4f秒' % (end_time - start_time))

        start_time = time.time()
        for i in range(repeat_times):
            cipher = rc4.encode_symmetrical(txt, key)
        end_time = time.time()
        logging.info(u'%d次加密耗时：%.4f秒' % (repeat_times, end_time - start_time))

        start_time = time.time()
        decr = rc4.decode_symmetrical(cipher, key)
        end_time = time.time()
        logging.info(u'单次解密耗时：%.4f秒' % (end_time - start_time))

        start_time = time.time()
        for i in range(repeat_times):
            decr = rc4.decode_symmetrical(cipher, key)
        end_time = time.time()
        logging.info(u'%d次解密耗时：%.4f秒' % (repeat_times, end_time - start_time))
        logging.info('=' * 100)


if __name__ == "__main__":
    unittest.main()
