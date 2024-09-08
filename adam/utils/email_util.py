#!python
# -*- coding:utf-8 -*-
"""
邮件公用函数(发邮件用)
Created on 2015/1/15
Updated on 2024/9/3
@author: Holemar

本模块专门供发邮件用,支持html内容及附件
"""
import os
import logging
import smtplib

from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formatdate
from email.header import Header

from .str_util import decode2str as to_unicode, decode2str as to_str

__all__ = ("send_mail",)

logger = logging.getLogger(__name__)

# 发邮件配置
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', 180))  # 超时时间(秒)
EMAIL_SERVER = os.environ.get('EMAIL_SERVER')  # SMTP server address
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 25))  # SMTP server port
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL') or False  # 是否使用 ssl 协议
EMAIL_USERNAME = os.environ.get('EMAIL_USERNAME')  # 发件人邮箱登陆账号
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')  # 发件人邮箱登陆密码
EMAIL_SENDER = os.environ.get('EMAIL_SENDER') or os.environ.get('EMAIL_USERNAME')  # 发件人邮箱地址

COMMASPACE = ', '

# 图片类型
TYPE_NAME = {
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "bmp": "application/x-bmp",
    "png": "image/png",
    "gif": "image/gif",
    "fax": "image/fax",
    "ico": "image/x-icon",
    "jfif": "image/jpeg",
    "jpe": "image/jpeg",
    "net": "image/pnetvue",
    "rp": "image/vnd.rn-realpix",
    "tif": "image/tiff",
    "tiff": "image/tiff",
    "wbmp": "image/vnd.wap.wbmp",
}


def send_mail(host=EMAIL_SERVER, user=EMAIL_USERNAME, password=EMAIL_PASSWORD, port=EMAIL_PORT, use_ssl=EMAIL_USE_SSL,
              From=EMAIL_SENDER, to_list=None, **kwargs):
    """
    发邮件
    :param {string} host: 连接smtp服务器
    :param {string} user: 登陆账号
    :param {string} password: 登陆密码
    :param {int} port: 连接smtp服务器的端口号,默认是 25
    :param {bool} use_ssl: 是否使用 ssl 协议连接smtp服务器, 使用之后的默认端口是 465
    :param {string} From: 收到信时显示的发信人设置，如："测试邮件<daillo@163.com>"

    :param {list} to_list: 收信人列表, 如： ["收件人1 <to1@qq.com>", "to2@qq.com"]
    :param {string} Cc: 抄送人, 多人用英文逗号分开, 如："cc1@163.com, cc2@163.com"
    :param {string} BCc: 暗抄邮箱(有抄送效果,但抄送人列表不展示), 多人用英文逗号分开, 如："bcc1@163.com, bcc2@163.com"
    :param {string} Subject: 邮件主题
    :param {string} html: HTML 格式的邮件正文内容
    :param {string} text: 纯文本 格式的邮件正文内容(html格式的及纯文本格式的，只能传其中一个，以html参数优先)
    :param {list} files: 附件列表,需填入附件路径,或者文件名及文件二进制流,如：["d:\\123.txt"]
                         或者 [{"file_content":open("d:\\123.txt", 'rb').read(), "file_name":"123.txt"}]
    :return {bool}: 发信成功则返回 True,否则返回 False
    """
    # 添加邮件内容
    msg = MIMEMultipart()
    msg['Date'] = formatdate(localtime=True)

    # 发信人
    from_address = to_str(From or '')
    msg['From'] = from_address

    # 邮件主题
    Subject = kwargs.get('Subject')
    if Subject:
        msg['Subject'] = Header(to_str(Subject), 'utf-8')  # 转编码,以免客户端看起来是乱码的

    # 邮件正文内容
    html = kwargs.get('html')
    text = kwargs.get('text')
    # HTML 格式的邮件正文内容
    if html:
        html = to_str(html)
        msg.attach(MIMEText(html, _subtype='html', _charset='utf-8'))
    # 纯文本 格式的邮件正文内容
    elif text:
        text = to_str(text)
        msg.attach(MIMEText(text, _subtype='plain', _charset='utf-8'))

    # 收信人列表
    if isinstance(to_list, str):
        to_list = [to_list]
    assert type(to_list) == list
    to_address = [to_str(to) for to in to_list]
    msg['To'] = COMMASPACE.join(to_address)  # COMMASPACE==', '  # 收件人邮箱, 多人逗号分开

    # 抄送人, 多人用英文逗号分开
    cc_address = kwargs.get('Cc')
    if cc_address:
        msg['Cc'] = to_str(cc_address)
    # 暗抄邮箱, 多人用英文逗号分开
    bcc_address = kwargs.get('BCc')
    if bcc_address:
        msg['BCc'] = to_str(bcc_address)

    # 添加附件
    if 'files' in kwargs:
        files = kwargs.get('files') or []
        index = 0
        for file_path in files:
            if isinstance(file_path, str):
                # 文件路径
                file_path = to_unicode(file_path)
                # 文件内容
                fb = open(file_path, 'rb')
                file_content = fb.read()
                fb.close()
                # 文件名(不包含路径)
                file_name = os.path.basename(file_path)
            # 传过来文件二进制流
            elif isinstance(file_path, dict):
                file_content = file_path['file_content']
                file_name = file_path['file_name']
            else:
                raise ValueError('files参数错误, 请检查')

            # 取文件后缀
            suffix = file_name.split('.')[-1]
            suffix = suffix.lower()
            # 处理图片附件
            if suffix in TYPE_NAME:
                index += 1
                mime = MIMEImage(file_content)
                mime.add_header('Content-ID', '<image%d>' % index)
                mime.add_header('Content-Type', TYPE_NAME.get(suffix, "image/" + suffix))
            # 传送 txt 文件
            elif suffix == 'txt':
                mime = MIMEText(file_content, _subtype='base64', _charset='utf-8')
                mime["Content-Type"] = 'application/octet-stream'
            # 其它附件
            else:
                mime = MIMEBase('application', 'octet-stream')  # 'octet-stream': binary data
                mime.set_payload(file_content)
                encoders.encode_base64(mime)
            mime.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', file_name))
            msg.attach(mime)

    # 发送邮件
    try:
        use_ssl = use_ssl if isinstance(use_ssl, bool) else (use_ssl and use_ssl.lower() == 'true')
        if use_ssl:
            port = port or 465
            smtp = smtplib.SMTP_SSL(timeout=EMAIL_TIMEOUT)
        else:
            port = port or 25
            smtp = smtplib.SMTP(timeout=EMAIL_TIMEOUT)
        smtp.connect(host, int(port))  # 连接 smtp 服务器
        smtp.login(user, password)  # 登陆服务器
        smtp.sendmail(from_address, to_address, msg.as_string())  # 发送邮件
        # smtp.close()
        smtp.quit()

        return True
    except smtplib.SMTPException as err:
        logger.error('发邮件出现 SMTPException 错误: %s', err, exc_info=True)
        return False
    except Exception as e:
        logger.error('发邮件错误:%s', e, exc_info=True)
        return False


if __name__ == '__main__':
    # 邮件配置
    host = "smtp.163.com"
    user = "daillo@163.com"
    password = "JBQTICDNAMIQJLBO"
    text = """请查收验证码:<font color='red'>88593</font>
    """
    res = send_mail(
        host=host, user=user, password=password,
        port=25,  # 默认端口
        use_ssl=False,  # 是否使用 ssl 协议, 使用之后的默认端口是 465。 不使用 ssl 协议时，端口号为 25
        From="富穆邮件<daillo@163.com>",
        to_list=["292598441@qq.com", 'daillow@qq.com'],  # 收件人列表,发多个人需要用列表,只用字符串则只发第一个
        Subject="测试邮件。。。",
        # Cc='415372820@qq.com', # 抄送人
        html=text,  # 邮件内容
        files=[  # 附件列表
            __file__,
            # {'file_name': u'备忘.txt', 'file_content': open(u'C:\\workspace\\备忘.txt', 'rb').read()}
            # 'C:\\workspace\\备忘.txt', # 中文名称的文件名，会导致显示乱码，暂时无法解决
        ]
    )
    if res:
        print("发送成功")
    else:
        print("发送失败")
