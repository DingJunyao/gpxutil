import asyncio
import uuid

import gpxpy
from beanie import PydanticObjectId
from beanie.operators import In
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, Path
from fastapi.responses import JSONResponse

from src.gpxutil.models.route import Route
from src.gpxutil_server.models.enum_model import CoordinateType
from src.gpxutil_server.models.route_entity import RouteMongoEntity, RoutePointMongoEntity
from src.gpxutil_server.util.route_util import set_route_point_area, set_route_point_area_background, \
    process_route_area, process_route_coordinate

router = APIRouter(prefix="/route", tags=["route"])


@router.put(
    '/from_gpx',
    name='导入 GPX',
    description = '从 GPX 文件写入数据'
)
async def upload_from_gpx(
        name: str = Form(default='', title='路径名称', description='要上传的路径的名称'),
        description: str = Form(default='', title='路径介绍', description='要上传的路径的介绍'),
        gpx_file: UploadFile = File(title='GPX 文件', description='要上传的 GPX 文件'),
        track_index: int = Form(default=0, title='轨迹序号', description='要上传的 GPX 文件的轨迹序号'),
        segment_index: int = Form(default=0, title='段落序号', description='要上传的 GPX 文件的段落序号'),
        transform_coordinate: bool = Form(default=False, title='是否转换坐标', description='是否转换坐标'),
        coordinate_type: CoordinateType = Form(default='wgs84', title='坐标类型', description='文件中的坐标类型'),
        transformed_coordinate_type: CoordinateType = Form(default='wgs84', title='转换后坐标类型', description='要转换的坐标类型'),
        set_area: bool = Form(default=False, title='是否填写行政区划', description='是否填写行政区划'),
) -> JSONResponse:
    gpx_content = await gpx_file.read()
    gpx = gpxpy.parse(gpx_content)
    route = Route.from_gpx_obj(
        gpx, track_index, segment_index, transform_coordinate=False, coordinate_type=coordinate_type.value, transformed_coordinate_type=transformed_coordinate_type.value, set_area=False
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

@router.get('/{route_id}', name='获取单个路径主信息', description='获取给定路径的主信息')
async def get_route(route_id: PydanticObjectId = Path(title='路径 ID', description='要获取的路径 ID')) -> RouteMongoEntity:
    route_entity = await RouteMongoEntity.get(route_id)
    return route_entity

@router.get('/', name='获取全部路径主信息', description='获取全部路径的主信息')
async def get_all_route() -> list[RouteMongoEntity]:
    route_entity_list = await RouteMongoEntity.find_all().to_list()
    return route_entity_list

@router.delete('/{route_id}', name='删除路径', description='删除路径，目前是硬删除，而且只删除了主信息')
async def delete_route(route_id: PydanticObjectId = Path(title='路径 ID', description='要删除的路径 ID')) -> JSONResponse:
    route_entity = await RouteMongoEntity.get(route_id)
    await route_entity.delete()
    return JSONResponse(content={'message': 'success'})

@router.post('/{route_id}/', name='更新路径主信息', description='更新路径的主信息')
async def update_route(
        route_id: PydanticObjectId = Path(title='路径 ID', description='要更新的路径 ID'),
        name: str = Form(default='', title='路径名称', description='要更改为的路径名称'),
        description: str = Form(default='', title='路径介绍', description='要更改为的路径介绍')
) -> JSONResponse:
    route_entity = await RouteMongoEntity.get(route_id)
    route_entity.name = name
    route_entity.description = description
    await route_entity.save()
    return JSONResponse(content={'message': 'success'})

@router.get('/{route_id}/points', name='获取单个路径的所有点信息',  description='获取单个路径的所有点信息')
async def get_route_points(route_id: PydanticObjectId = Path(title='路径 ID', description='要获取的路径 ID')) -> list[RoutePointMongoEntity]:
    point_entities = await RoutePointMongoEntity.find(RoutePointMongoEntity.route_id == route_id).sort(RoutePointMongoEntity.index).to_list()
    return point_entities

@router.get('/point/{point_id}', name='获取单个点信息', description='获取单个点信息')
async def get_point(point_id: PydanticObjectId = Path(title='点 ID', description='要获取的点 ID')):
    point = await RoutePointMongoEntity.get(point_id)
    return point

@router.post('/point/{point_id}/area', name='点写入行政区划', description='给指定点写入行政区划')
async def set_point_area(point_id: PydanticObjectId = Path(title='点 ID', description='要更改的点 ID')):
    await set_route_point_area(point_id)
    return JSONResponse(content={'message': 'success'})
    # task = set_route_point_area_background.delay(str(point_id))
    # return JSONResponse(content={'message': 'success', 'task_id': task.id})


@router.post('/point/{point_id}/coordinate', name='点转换坐标', description='给指定点转换坐标')
async def transform_point_coordinate(point_id: PydanticObjectId = Path(title='点 ID', description='要更改的点 ID')):
    point_entity = await RoutePointMongoEntity.get(point_id)
    await point_entity.transform_coordinate_from_parent()
    await point_entity.replace()
    return JSONResponse(content={'message': 'success'})
    # task = set_route_point_area_background.delay(str(point_id))
    # return JSONResponse(content={'message': 'success', 'task_id': task.id})


@router.post("/{route_id}/area", name='路径写入行政区划', description='给指定路径下的所有点写入行政区划')
async def set_route_area(route_id: PydanticObjectId = Path(title='路径 ID', description='要写入的路径 ID')):
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

@router.post("/{route_id}/coordinate", name='路径转换坐标', description='给指定路径下的所有点转换坐标')
async def transform_route_coordinate(route_id: PydanticObjectId = Path(title='路径 ID', description='要转换的路径 ID')):
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