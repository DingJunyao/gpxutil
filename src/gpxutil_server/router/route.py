import asyncio
import uuid

import gpxpy
from beanie import PydanticObjectId
from beanie.operators import In
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse

from src.gpxutil.models.route import Route
from src.gpxutil_server.models.route_entity import RouteMongoEntity, RoutePointMongoEntity
from src.gpxutil_server.util.route_util import set_route_point_area, set_route_point_area_background, \
    process_route_area, process_route_coordinate

router = APIRouter(prefix="/route", tags=["route"])


@router.put('/from_gpx')
async def upload_from_gpx(
        background_tasks: BackgroundTasks,
        name: str = Form(default=''),
        description: str = Form(default=''),
        gpx_file: UploadFile = File(),
        track_index: int = Form(default=0),
        segment_index: int = Form(default=0),
        transform_coordinate: bool = Form(default=False),
        coordinate_type: str = Form(default='wgs84'),
        transformed_coordinate_type: str = Form(default='wgs84'),
        set_area: bool = Form(default=False),
) -> JSONResponse:
    gpx_content = await gpx_file.read()
    gpx = gpxpy.parse(gpx_content)
    route = Route.from_gpx_obj(
        gpx, track_index, segment_index, transform_coordinate=False, coordinate_type=coordinate_type, transformed_coordinate_type=transformed_coordinate_type, set_area=False
    )

    route_entity = RouteMongoEntity.from_route_instance('admin', route, name, description)
    points = route_entity._temp_points
    # point_ids = [point.id for point in points]
    # route_entity.point_ids = point_ids
    del route_entity._temp_points
    await route_entity.create()
    route_id = str(route_entity.id)
    for point in points:
        point.route_id = route_id
    tasks = [point.create() for point in points]
    await asyncio.gather(*tasks)

    transform_coordinate_task_id = ''
    set_area_task_id = ''

    if transform_coordinate:
        transform_coordinate_task_id = str(uuid.uuid4())
        # 异步执行父任务
        process_route_coordinate.delay(
            task_id=transform_coordinate_task_id,
            route_id=str(route_id)
        )
    if set_area:
        set_area_task_id = str(uuid.uuid4())
        # 异步执行父任务
        process_route_area.delay(
            task_id=set_area_task_id,
            route_id=str(route_id)
        )
    return JSONResponse(
        content={
            'message': 'success',
            'route_id': str(route_entity.id),
            'tasks': {
                'transform_coordinate': transform_coordinate_task_id,
                'set_area': set_area_task_id
            }
        }
    )

@router.get('/{route_id}')
async def get_route(route_id: PydanticObjectId) -> RouteMongoEntity:
    route_entity = await RouteMongoEntity.get(route_id)
    return route_entity

@router.get('/')
async def get_all_route() -> list[RouteMongoEntity]:
    route_entity_list = await RouteMongoEntity.find_all().to_list()
    return route_entity_list

@router.delete('/{route_id}')
async def delete_route(route_id: PydanticObjectId) -> JSONResponse:
    route_entity = await RouteMongoEntity.get(route_id)
    await route_entity.delete()
    return JSONResponse(content={'message': 'success'})

@router.post('/{route_id}/')
async def update_route(route_id: PydanticObjectId, name: str = Form(default=''), description: str = Form(default='')) -> JSONResponse:
    route_entity = await RouteMongoEntity.get(route_id)
    route_entity.name = name
    route_entity.description = description
    await route_entity.save()
    return JSONResponse(content={'message': 'success'})

@router.get('/{route_id}/points')
async def get_route_points(route_id: PydanticObjectId) -> list[RoutePointMongoEntity]:
    point_entities = await RoutePointMongoEntity.find(RoutePointMongoEntity.route_id == route_id).to_list()
    return point_entities

@router.get('point/{point_id}')
async def get_point(point_id: PydanticObjectId):
    point = await RoutePointMongoEntity.get(point_id)
    return point

@router.post('point/{point_id}/area')
async def set_point_area(point_id: PydanticObjectId):
    await set_route_point_area(point_id)
    return JSONResponse(content={'message': 'success'})
    # task = set_route_point_area_background.delay(str(point_id))
    # return JSONResponse(content={'message': 'success', 'task_id': task.id})


@router.post('point/{point_id}/coordinate')
async def transform_point_coordinate(point_id: PydanticObjectId):
    point_entity = await RoutePointMongoEntity.get(point_id)
    await point_entity.transform_coordinate_from_parent()
    await point_entity.replace()
    return JSONResponse(content={'message': 'success'})
    # task = set_route_point_area_background.delay(str(point_id))
    # return JSONResponse(content={'message': 'success', 'task_id': task.id})


@router.post("/{route_id}/area")
async def set_route_area(route_id: PydanticObjectId):
    # route_entity = await RouteMongoEntity.get(route_id)
    # task_ids = [set_route_point_area_background.delay(str(point_id)).id for point_id in route_entity.point_ids]
    # return JSONResponse(content={'message': 'success', 'task_id': task_ids})
    route_entity = await RouteMongoEntity.get(route_id)

    # 创建唯一任务ID
    task_id = str(uuid.uuid4())

    # 异步执行父任务
    process_route_area.delay(
        task_id=task_id,
        route_id = str(route_id)
    )

    return JSONResponse(content={'message': 'Area processing started', 'task_id': task_id})

@router.post("/{route_id}/coordinate")
async def transform_route_coordinate(route_id: PydanticObjectId):
    # route_entity = await RouteMongoEntity.get(route_id)
    # task_ids = [set_route_point_area_background.delay(str(point_id)).id for point_id in route_entity.point_ids]
    # return JSONResponse(content={'message': 'success', 'task_id': task_ids})

    # 创建唯一任务ID
    task_id = str(uuid.uuid4())

    # 异步执行父任务
    process_route_coordinate.delay(
        task_id=task_id,
        route_id = str(route_id)
    )

    return JSONResponse(content={'message': 'Coordinate processing started', 'task_id': task_id})