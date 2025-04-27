import sqlite3
from contextlib import contextmanager
from functools import partial

from src.gpxutil.core.config import CONFIG_HANDLER


@contextmanager
def auto_connect(database, conn=None):
    is_new_connection = False
    try:
        if conn is None:
            conn = sqlite3.connect(database)
            is_new_connection = True
        yield conn  # 返回连接供方法使用
    finally:
        if is_new_connection and conn is not None:
            conn.close()

auto_connect_area_db = partial(auto_connect, CONFIG_HANDLER.config.area_info.area_info_sqlite_path)