import asyncio
import traceback
from datetime import datetime

from beanie import PydanticObjectId
from celery import chain, group
from loguru import logger

from src.gpxutil_server.core.celery_conf import celery_app
from src.gpxutil_server.core.db import REDIS_CLIENT
from src.gpxutil_server.models.route_entity import RoutePointMongoEntity
from src.gpxutil_server.models.route_entity_sync import RoutePointMongoSyncEntity, RouteMongoSyncEntity


async def set_route_point_area(route_point_id: PydanticObjectId):
    route_point_entity = await RoutePointMongoEntity.get(route_point_id)
    route_point_entity.set_area()
    await route_point_entity.replace()

@celery_app.task
def set_route_point_area_background(route_point_id: str, task_id: str):  # 注意这里是 str 不是 PydanticObjectId
    try:
        oid = PydanticObjectId(route_point_id)
        route_point_entity = RoutePointMongoSyncEntity.get(oid).run()

        if not route_point_entity:
            logger.error(f"Route point not found: {route_point_id}")
            return

        route_point_entity.set_area()
        route_point_entity.replace()

        # 原子性更新进度
        with REDIS_CLIENT.pipeline() as pipe:
            pipe.hincrby(f"task_progress:{task_id}", "completed", 1)
            pipe.hset(f"task_progress:{task_id}", "last_update", datetime.now().isoformat())
            pipe.execute()

    except Exception as e:
        # 错误处理（可额外记录错误信息）
        logger.error(f"Task failed: {task_id}, point: {route_point_id} - {str(e)} \n ")
        traceback.print_exc()
        
        # 更新错误计数
        with REDIS_CLIENT.pipeline() as pipe:
            pipe.hincrby(f"task_progress:{task_id}", "error", 1)
            pipe.hset(f"task_progress:{task_id}", "last_update", datetime.now().isoformat())
            pipe.execute()


@celery_app.task
def process_route_area(task_id: str, route_id: str):
    oid = PydanticObjectId(route_id)
    route_entity: RouteMongoSyncEntity = RouteMongoSyncEntity.get(oid).run()
    route_points = RoutePointMongoSyncEntity.find(RoutePointMongoSyncEntity.route_id == route_id).run()
    point_ids = [point.id for point in route_points]
    # 初始化任务进度
    REDIS_CLIENT.hset(
        f"task_progress:{task_id}",
        mapping={
            "total": len(point_ids),
            "completed": 0,
            "error": 0,
            "start_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat()
        }
    )

    # 设置任务过期时间（24小时）
    REDIS_CLIENT.expire(f"task_progress:{task_id}", 60 * 60 * 24)

    # 创建子任务链
    task_chain = group(
        [set_route_point_area_background.si(str(point_id), task_id)
         for point_id in point_ids]
    )

    task_chain.apply_async()

async def transform_coordinate(route_point_id: PydanticObjectId):
    point_entity = await RoutePointMongoEntity.get(route_point_id)
    await point_entity.transform_coordinate_from_parent()
    await point_entity.replace()

# def transform_coordinate_background(route_point_id: PydanticObjectId):
#     point_entity = RoutePointMongoSyncEntity.get(route_point_id).run()
#     point_entity.transform_coordinate_from_parent()
#     point_entity.replace()


@celery_app.task
def transform_coordinate_background(
        route_point_id: str, original_coordinate_type: str, transformed_coordinate_type: str,
        task_id: str
):  # 注意这里是 str 不是 PydanticObjectId
    try:
        oid = PydanticObjectId(route_point_id)
        route_point_entity: RoutePointMongoSyncEntity = RoutePointMongoSyncEntity.get(oid).run()

        if not route_point_entity:
            logger.error(f"Route point not found: {route_point_id}")
            return

        route_point_entity.transform_coordinate(original_coordinate_type, transformed_coordinate_type)
        route_point_entity.replace()

        # 原子性更新进度
        with REDIS_CLIENT.pipeline() as pipe:
            pipe.hincrby(f"task_progress:{task_id}", "completed", 1)
            pipe.hset(f"task_progress:{task_id}", "last_update", datetime.now().isoformat())
            pipe.execute()

    except Exception as e:
        # 错误处理（可额外记录错误信息）
        logger.error(f"Task failed: {task_id}, point: {route_point_id} - {str(e)} \n ")
        traceback.print_exc()

        # 更新错误计数
        with REDIS_CLIENT.pipeline() as pipe:
            pipe.hincrby(f"task_progress:{task_id}", "error", 1)
            pipe.hset(f"task_progress:{task_id}", "last_update", datetime.now().isoformat())
            pipe.execute()


@celery_app.task
def process_route_coordinate(task_id: str, route_id: str):
    oid = PydanticObjectId(route_id)
    route_entity: RouteMongoSyncEntity = RouteMongoSyncEntity.get(oid).run()
    route_points = RoutePointMongoSyncEntity.find(RoutePointMongoSyncEntity.route_id == route_id).run()
    point_ids = [point.id for point in route_points]
    # 初始化任务进度
    REDIS_CLIENT.hset(
        f"task_progress:{task_id}",
        mapping={
            "total": len(point_ids),
            "completed": 0,
            "error": 0,
            "start_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat()
        }
    )

    # 设置任务过期时间（24小时）
    REDIS_CLIENT.expire(f"task_progress:{task_id}", 60 * 60 * 24)

    # 创建子任务链
    task_chain = group(
        [transform_coordinate_background.si(
            str(point_id), route_entity.coordinate_type, route_entity.transformed_coordinate_type,
            task_id
        )
         for point_id in point_ids]
    )

    task_chain.apply_async()