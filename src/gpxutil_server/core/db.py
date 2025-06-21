import asyncio
import atexit
import threading

import motor.motor_asyncio
import redis
from beanie import init_beanie
from bunnet import init_bunnet
from loguru import logger
from pymongo import MongoClient

from src.gpxutil_server.core.config import ConfigHandler
from src.gpxutil_server.models.route_entity import *
from src.gpxutil_server.models.route_entity_sync import RoutePointMongoSyncEntity, RouteMongoSyncEntity


async def init_mongodb():
    config = ConfigHandler().config
    client = motor.motor_asyncio.AsyncIOMotorClient(
        f"mongodb://{config.mongodb.host}:{config.mongodb.port}/",
    )

    await init_beanie(
        database=client[config.mongodb.db],
        document_models=[RoutePointMongoEntity, RouteMongoEntity]
    )

def init_mongodb_sync():
    config = ConfigHandler().config
    client = MongoClient(
        f"mongodb://{config.mongodb.host}:{config.mongodb.port}/",
    )

    # Initialize bunnet with the Product document class
    print("Initialize bunnet")
    init_bunnet(database=client[config.mongodb.db], document_models=[RoutePointMongoSyncEntity, RouteMongoSyncEntity])

class RedisHandler:
    _instance_lock = threading.Lock()
    _instance = None  # 显式声明类变量用于存储单例实例
    _initialized = False  # 类变量用于跟踪是否已初始化

    def __init__(self, config_path: str = None):
        if not RedisHandler._initialized:
            self.conn = self.load()
            RedisHandler._initialized = True  # 标记为已初始化
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
            logger.info(f"Redis connection closed")
            # 防止重复关闭
            self.conn = None

    def __del__(self):
        # 析构函数作为最后保障（但不要完全依赖它）
        self.close()

    def load(self):
        config = ConfigHandler().config
        conn = redis.StrictRedis(host=config.redis.host, port=config.redis.port, db=config.redis.db)
        return conn

REDIS_CLIENT = RedisHandler().conn