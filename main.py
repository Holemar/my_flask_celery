# -*- coding: utf-8 -*-
import os
import logging

import settings
from adam.flask_app import Adam

logger = logging.getLogger(__name__)

app = Adam(
    static_folder=os.path.join(settings.CURRENT_DIR, 'static/'),
    enable_celery=True,
)


if __name__ == '__main__':
    # 程序启动
    app.run(debug=settings.DEBUG)
else:
    # 程序运行在uwsgi服务器上
    from gevent import monkey
    from adam.utils.log_filter import add_file_handler
    monkey.patch_all()
    add_file_handler('logs/api.log', 'INFO')

