# -*- coding: utf-8 -*-
import os
import logging

import settings
from utils.flask_app import Adam
from views import index

logger = logging.getLogger(__name__)

app = Adam(
    static_folder=os.path.join(settings.CURRENT_DIR, 'static/'),
    enable_celery=True,
)
app.register_blueprint(index.bp, url_prefix="")


if __name__ == '__main__':
    # 程序启动
    app.run()
