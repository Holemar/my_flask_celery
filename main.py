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
    # 程序运行在wsgi服务器上
    app.init_wsgi_server()

