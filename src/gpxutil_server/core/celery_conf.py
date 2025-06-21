# 运行命令：
# celery -A src.gpxutil_server.core.celery_conf worker --loglevel=info --pool=solo

import requests
from beanie import init_beanie
from bunnet import init_bunnet
from celery import Celery
from celery.signals import worker_ready
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from src.gpxutil.utils.db_connect import AreaCodeConnectHandler
from src.gpxutil.utils.gdf_handler import GDFListHandler
from src.gpxutil_server.core.config import ConfigHandler
from src.gpxutil_server.core.db import init_mongodb_sync
from src.gpxutil_server.models.route_entity_sync import RoutePointMongoSyncEntity, RouteMongoSyncEntity

config = ConfigHandler().config

# def init_mongodb_sync():
#     print("Connecting to MongoDB at", config.mongodb.host, "port", config.mongodb.port)
#
#     client = MongoClient(
#         f"mongodb://localhost:27017/",
#         connectTimeoutMS=60000,
#         socketTimeoutMS=60000
#     )
#
#     try:
#         print("Ping MongoDB...")
#         client.admin.command('ping')  # 主动测试连接
#         print("Connected successfully.")
#     except Exception as e:
#         print("MongoDB connection failed:", str(e))
#         raise
#
#     print("Initializing Bunnet models...")
#     init_bunnet(database=client[config.mongodb.db], document_models=[
#         RoutePointMongoSyncEntity, RouteMongoSyncEntity
#     ])
#     print("Bunnet initialized.")

celery_app = Celery(
    'gpxutil_server',
    broker=f'redis://{config.redis.host}:{config.redis.port}/{config.redis.db}',
    include=['src.gpxutil_server.util.route_util']
)

celery_app.conf.update(
    result_expires=3600,
)

@worker_ready.connect
def on_worker_ready(**kwargs):
    print("Worker is ready. Initializing MongoDB sync...")
    GDFListHandler()
    AreaCodeConnectHandler()
    init_mongodb_sync()

if __name__ == '__main__':
    celery_app.start()