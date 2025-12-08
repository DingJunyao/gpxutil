import sqlite3
import threading
import atexit
from loguru import logger

from src.gpxutil.core.config import CONFIG_HANDLER


# @contextmanager
# def auto_connect(database, conn=None):
#     is_new_connection = False
#     try:
#         if conn is None:
#             conn = sqlite3.connect(database)
#             is_new_connection = True
#         yield conn  # 返回连接供方法使用
#     finally:
#         if is_new_connection and conn is not None:
#             conn.close()
#
# auto_connect_area_db = partial(auto_connect, CONFIG_HANDLER.config.area_info.area_info_sqlite_path)

class DbConnectHandler:
    _instance_lock = threading.Lock()
    _instance = None
    _initialized = False

    def __init__(self, database=None):
        self.database = database
        if not DbConnectHandler._initialized:
            self.conn = self.load()
            DbConnectHandler._initialized = True
            # 注册程序退出时的关闭函数
            atexit.register(self.close)

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._instance_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def close(self):
        """显式关闭数据库连接"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            logger.info(f"SQLite DB closed: {self.database}")
            # 防止重复关闭
            self.conn = None

    def __del__(self):
        # 析构函数作为最后保障（但不要完全依赖它）
        self.close()

    def load(self):
        return sqlite3.connect(self.database)

class AreaCodeConnectHandler(DbConnectHandler):
    if CONFIG_HANDLER.config.area_info.gdf is not None:
        def __init__(self, database=CONFIG_HANDLER.config.area_info.gdf.area_info_sqlite_path):
            super().__init__(database)
    else:
        logger.warning('No gdf config')