import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from beanie import Document, PydanticObjectId

from src.gpxutil.models.route import Route, RoutePoint
from src.gpxutil.utils.db_connect import AreaCodeConnectHandler
from src.gpxutil.utils.gdf_handler import GDFListHandler


class RoutePointMongoEntity(Document):

    route_id: Optional[PydanticObjectId] = None
    
    """
    行程的点
    """
    index: Optional[int] = None

    time: Optional[datetime] = None
    """时间"""

    elapsed_time: Optional[float] = None
    """经过的秒数"""
    #
    # coordinate_type: Optional[str] = None
    # """原始类型"""

    longitude: Optional[float] = None
    """经度"""

    latitude: Optional[float] = None
    """纬度"""
    #
    # transformed_coordinate_type: Optional[str] = None
    # """坐标转换后类型"""

    longitude_transformed: Optional[float] = None
    """转换后的经度"""

    latitude_transformed: Optional[float] = None
    """转换后的纬度"""

    elevation: Optional[float] = None
    """高度"""

    distance: Optional[float] = None
    """距离"""

    course: Optional[float] = None
    """方向"""

    speed: Optional[float] = None
    """速度"""

    province: Optional[str] = None
    """省"""

    city: Optional[str] = None
    """市"""

    area: Optional[str] = None
    """县/区"""

    province_en: Optional[str] = None
    """省英文"""

    city_en: Optional[str] = None
    """市英文"""

    area_en: Optional[str] = None
    """县/区英文"""

    road_num: Optional[str] = None
    """道路编号"""

    road_name: Optional[str] = None
    """道路名称"""

    road_name_en: Optional[str] = None
    """道路名称英文"""

    memo: Optional[str] = None
    """备注"""

    class Settings:
        name = "route_point"

    @staticmethod
    def from_route_point_instance(route_point_instance: RoutePoint):
        return RoutePointMongoEntity(
            index=route_point_instance.index,
            time=route_point_instance.time,
            elapsed_time=route_point_instance.elapsed_time,
            # coordinate_type=route_point_instance.coordinate_type,
            longitude=route_point_instance.longitude,
            latitude=route_point_instance.latitude,
            # transformed_coordinate_type=route_point_instance.transformed_coordinate_type,
            longitude_transformed=route_point_instance.longitude_transformed,
            latitude_transformed=route_point_instance.latitude_transformed,
            elevation=route_point_instance.elevation,
            distance=route_point_instance.distance,
            course=route_point_instance.course,
            speed=route_point_instance.speed,
            province=route_point_instance.province,
            city=route_point_instance.city,
            area=route_point_instance.area,
            province_en=route_point_instance.province_en,
            city_en=route_point_instance.city_en,
            area_en=route_point_instance.area_en,
            road_num=route_point_instance.road_num,
            road_name=route_point_instance.road_name,
            road_name_en=route_point_instance.road_name_en,
            memo=route_point_instance.memo
        )

    def to_route_point_instance(self) -> RoutePoint:
        return RoutePoint(
            index=self.index,
            time=self.time,
            elapsed_time=self.elapsed_time,
            longitude=self.longitude,
            latitude=self.latitude,
            longitude_transformed=self.longitude_transformed,
            latitude_transformed=self.latitude_transformed,
            elevation=self.elevation,
            distance=self.distance,
            course=self.course,
            speed=self.speed,
            province=self.province,
            city=self.city,
            area=self.area,
            province_en=self.province_en,
            city_en=self.city_en,
            area_en=self.area_en,
            road_num=self.road_num,
            road_name=self.road_name,
            road_name_en=self.road_name_en,
            memo=self.memo
        )

    def set_area(self):
        point_entity = self.to_route_point_instance()
        point_entity.set_area(area_gdf_list=GDFListHandler().list, area_code_conn=AreaCodeConnectHandler().get_connection(), force=True)
        self.province = point_entity.province
        self.city = point_entity.city
        self.area = point_entity.area

    def transform_coordinate(self, coordinate_type, transformed_coordinate_type):
        point_entity = self.to_route_point_instance()
        point_entity.transform_coordinate(coordinate_type, transformed_coordinate_type, force=True)
        self.longitude_transformed = point_entity.longitude_transformed
        self.latitude_transformed = point_entity.latitude_transformed

    async def transform_coordinate_from_parent(self):
        point_entity = self.to_route_point_instance()
        parent_route = await RouteMongoEntity.get(self.route_id)
        point_entity.transform_coordinate(parent_route.coordinate_type, parent_route.transformed_coordinate_type, force=True)
        self.longitude_transformed = point_entity.longitude_transformed
        self.latitude_transformed = point_entity.latitude_transformed


class RouteMongoEntity(Document):
    username: Optional[str]
    create_time: datetime
    update_time: datetime
    name: Optional[str]
    description: Optional[str]

    # point_ids: list[PydanticObjectId] = []
    # """行程中的点"""

    coordinate_type: Optional[str] = None
    """原始类型"""

    transformed_coordinate_type: Optional[str] = None
    """坐标转换后类型"""

    # _temp_points: list[RoutePointMongoEntity] = []

    class Settings:
        name = "route"

    @classmethod
    def from_route_instance(
            cls,
            username: str,
            route: Route,
            name: str = '',
            description: str = ''
    ):
        create_time = datetime.now()
        update_time = create_time
        route_points = [RoutePointMongoEntity.from_route_point_instance(point) for point in route.points]
        return cls(
            username=username, create_time=create_time, update_time=update_time,
            name=name, description=description, coordinate_type=route.coordinate_type,
            transformed_coordinate_type=route.transformed_coordinate_type, point_entities=route_points
        )

    def __init__(self, *args, point_entities=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._temp_points = point_entities

    async def to_route_instance(self):
        points = await RoutePointMongoEntity.find(RoutePointMongoEntity.route_id == self.id).to_list()
        return Route(
            points=[point.to_route_point_instance() for point in points],
            coordinate_type=self.coordinate_type,
            transformed_coordinate_type=self.transformed_coordinate_type
        )