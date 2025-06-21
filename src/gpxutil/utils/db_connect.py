import sqlite3
import threading
import atexit
from loguru import logger
from dbutils.pooled_db import PooledDB

from src.gpxutil.core.config import CONFIG_HANDLER


class DbConnectHandler:
    _instance_lock = threading.Lock()
    _pools = {}  # 存储不同数据库的连接池
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_singleton_instance'):
            with cls._instance_lock:
                if not hasattr(cls, '_singleton_instance'):
                    cls._singleton_instance = super().__new__(cls)
        return cls._singleton_instance

    def __init__(self, database=None):
        self.database = database
        if not DbConnectHandler._initialized:
            self.pool = self.get_or_create_pool(database)
            DbConnectHandler._initialized = True
            atexit.register(self.close_all)

    def get_or_create_pool(self, database):
        """创建或获取一个连接池"""
        if database in DbConnectHandler._pools:
            return DbConnectHandler._pools[database]
        pool = PooledDB(
            creator=sqlite3,
            database=database,
            check_same_thread=False,
            maxconnections=5,  # 最大连接数
            blocking=True      # 超出连接数后是否等待释放
        )
        DbConnectHandler._pools[database] = pool
        logger.info(f"SQLite 连接池已初始化: {database}")
        return pool

    def get_connection(self):
        """从连接池中获取一个连接"""
        conn = self.pool.connection()
        # logger.info(f"获取一个 SQLite 连接，来自池: {self.database}")
        return conn

    def close_all(self):
        """关闭所有连接池中的连接"""
        for db, pool in DbConnectHandler._pools.items():
            try:
                pool.close()
                logger.info(f"SQLite 连接池已关闭: {db}")
            except Exception as e:
                logger.error(f"关闭连接池失败: {e}")
        DbConnectHandler._pools.clear()

    def __del__(self):
        self.close_all()


class AreaCodeConnectHandler(DbConnectHandler):
    def __init__(self, database=CONFIG_HANDLER.config.area_info.area_info_sqlite_path):
        super().__init__(database)

    def get_connection(self):
        return super().get_connection()