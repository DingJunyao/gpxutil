import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

import gpxpy
from geopandas import GeoDataFrame
from shapely.geometry.point import Point
from tqdm import tqdm

from src.gpxutil.utils import csv_util
from src.gpxutil.utils.data_type_processor import process_or_none, float_or_none
from src.gpxutil.utils.datetime_util import datetime_yyyymmdd_slash_time_microsecond_tz
from src.gpxutil.utils.db_connect import AreaCodeConnectHandler
from src.gpxutil.utils.gdf_handler import GDFListHandler
from src.gpxutil.utils.nominatim import get_point_info
from src.gpxutil.utils.route_util import calculate_bearing, get_area_info
from src.gpxutil.utils.gpx_convert import convert_single_point


@dataclass
class RoutePoint:
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

    def set_area(self, from_nominatim: bool = True, area_gdf_list: list[GeoDataFrame] = None, area_code_conn: sqlite3.Connection = None, force: bool = False):
        """
        填写行政区划。目前的做法是：加载各地区的 geojson 文件（area_gdf_list），判断点属于哪个地区的，得到代码，在给定的 SQLite 文件中找到对应代码的行政区划。
        :param area_gdf_list: 各地区的 geojson 文件转换为 GeoDataFrame 后的列表
        :param area_code_conn: 存放行政区划代码关系的 SQLite 数据库连接
        :param force: 对已经填写地区的点，是否覆盖内容
        :return: None
        """
        if self.province is not None and self.city is not None and self.area is not None and not force:
            return
        if from_nominatim:
            area_info = get_point_info(self.longitude, self.latitude)
            province_result, city_result, area_result, town_result, road_name_result, road_num_result, province_en_result, city_en_result, area_en_result, town_en_result, road_name_en_result, memo_result = area_info
            if self.province != province_result:
                self.province_en = None
            if self.city != city_result:
                self.city_en = None
            if self.area != area_result:
                self.area_en = None
            if self.road_name != road_name_result:
                self.road_name_en = None
            self.province = province_result
            self.city = city_result
            self.area = area_result
            self.road_name = road_name_result
            self.road_num = road_num_result
            if force:
                self.province_en = province_en_result
                self.city_en = city_en_result
                self.area_en = area_en_result
                self.road_name_en = road_name_en_result
        else:
            area_info = get_area_info(Point(self.longitude, self.latitude), area_gdf_list = area_gdf_list, area_code_conn = area_code_conn)
            province_result = area_info[0] if area_info is not None else None
            city_result = area_info[1] if area_info is not None else None
            area_result = area_info[2] if area_info is not None else None
            if self.province != province_result:
                self.province_en = None
            if self.city != city_result:
                self.city_en = None
            if self.area != area_result:
                self.area_en = None
            self.province = province_result
            self.city = city_result
            self.area = area_result

    def transform_coordinate(self, coordinate_type, transformed_coordinate_type, force: bool = False):
        """
        转换坐标。转换结果放在 longitude_transformed、latitude_transformed
        :param coordinate_type: 原坐标类型
        :param transformed_coordinate_type: 要转换为的坐标类型
        :param force: 对已经填写转换后坐标的点，是否覆盖内容
        :return: None
        """
        if self.longitude_transformed is not None and self.latitude_transformed is not None and not force:
            return
        if coordinate_type == transformed_coordinate_type:
            return
        self.longitude_transformed, self.latitude_transformed = convert_single_point(self.longitude, self.latitude, coordinate_type, transformed_coordinate_type)

    def to_json_dict_obj(self) -> dict[str, Any]:
        """
        转换为能够转为 JSON 字符串的字典类型，供转为 JSON 使用。
        :return: dict[str, Any]
        """
        return {
            "index": self.index,
            "time": self.time.isoformat() if self.time is not None else None,
            "elapsed_time": self.elapsed_time,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "longitude_transformed": self.longitude_transformed,
            "latitude_transformed": self.latitude_transformed,
            "elevation": self.elevation,
            "distance": self.distance,
            "course": self.course,
            "speed": self.speed,
            "province": self.province,
            "city": self.city,
            "area": self.area,
            "province_en": self.province_en,
            "city_en": self.city_en,
            "area_en": self.area_en,
            "road_num": self.road_num,
            "road_name": self.road_name,
            "road_name_en": self.road_name_en,
            "memo": self.memo,
        }

    def to_csv_dict_obj(self) -> dict[str, Any]:
        """
        转换为能够转为 CSV 的字典类型，供转为 CSV，在诸如 Excel 的软件里面使用。
        其中的日期和时间（时分秒）和毫秒会分开存储，以避免表格软件对时间的格式化损失数据。
        :return: dict[str, Any]
        """
        return {
            "index": self.index if self.index is not None else '',
            "time_date": self.time.date().strftime('%Y/%m/%d') if self.time is not None else '',
            "time_time": self.time.time().strftime('%H:%M:%S') if self.time is not None else '',
            "time_microsecond": self.time.time().microsecond if self.time is not None else '',
            "elapsed_time": self.elapsed_time if self.elapsed_time is not None else '',
            "longitude": self.longitude if self.longitude is not None else '',
            "latitude": self.latitude if self.latitude is not None else '',
            "longitude_transformed": self.longitude_transformed if self.longitude_transformed is not None else '',
            "latitude_transformed": self.latitude_transformed if self.latitude_transformed is not None else '',
            "elevation": self.elevation if self.elevation is not None else '',
            "distance": self.distance if self.distance is not None else '',
            "course": self.course if self.course is not None else '',
            "speed": self.speed if self.speed is not None else '',
            "province": self.province if self.province is not None else '',
            "city": self.city if self.city is not None else '',
            "area": self.area if self.area is not None else '',
            "province_en": self.province_en if self.province_en is not None else '',
            "city_en": self.city_en if self.city_en is not None else '',
            "area_en": self.area_en if self.area_en is not None else '',
            "road_num": self.road_num if self.road_num is not None else '',
            "road_name": self.road_name if self.road_name is not None else '',
            "road_name_en": self.road_name_en if self.road_name_en is not None else '',
            "memo": self.memo if self.memo is not None else '',
        }


    @staticmethod
    def from_json_dict_obj(json_dict_obj) -> 'RoutePoint':
        """
        从 JSON 字典类转换。
        :param json_dict_obj: JSON 字典类
        :return: RoutePoint
        """
        return RoutePoint(
            index=json_dict_obj["index"],
            time=datetime.fromisoformat(json_dict_obj["time"]) if json_dict_obj["time"] is not None else None,
            elapsed_time=float_or_none(json_dict_obj["elapsed_time"]),
            longitude=float_or_none(json_dict_obj["longitude"]),
            latitude=float_or_none(json_dict_obj["latitude"]),
            longitude_transformed=float_or_none(json_dict_obj["longitude_transformed"]),
            latitude_transformed=float_or_none(json_dict_obj["latitude_transformed"]),
            elevation=float_or_none(json_dict_obj["elevation"]),
            distance=float_or_none(json_dict_obj["distance"]),
            course=float_or_none(json_dict_obj["course"]),
            speed=float_or_none(json_dict_obj["speed"]),
            province=json_dict_obj["province"],
            city=json_dict_obj["city"],
            area=json_dict_obj["area"],
            province_en=json_dict_obj["province_en"],
            city_en=json_dict_obj["city_en"],
            area_en=json_dict_obj["area_en"],
            road_num=json_dict_obj["road_num"],
            road_name=json_dict_obj["road_name"],
            road_name_en=json_dict_obj["road_name_en"],
            memo=json_dict_obj["memo"],
        )

    @staticmethod
    def from_csv_dict_obj(csv_dict_obj) -> 'RoutePoint':
        """
        从 CSV 字典类转换。
        :param csv_dict_obj: JSON 字典类
        :return: RoutePoint
        """
        return RoutePoint(
            index=process_or_none(csv_dict_obj["index"], int),
            time=datetime_yyyymmdd_slash_time_microsecond_tz(csv_dict_obj["time_date"], csv_dict_obj["time_time"], microsecond=int(csv_dict_obj["time_microsecond"]))
                    if csv_dict_obj["time_date"] is not None and csv_dict_obj["time_time"] is not None and csv_dict_obj["time_microsecond"] is not None
                    else None,
            elapsed_time=float_or_none(csv_dict_obj["elapsed_time"]),
            longitude=float_or_none(csv_dict_obj["longitude"]),
            latitude=float_or_none(csv_dict_obj["latitude"]),
            longitude_transformed=float_or_none(csv_dict_obj["longitude_transformed"]),
            latitude_transformed=float_or_none(csv_dict_obj["latitude_transformed"]),
            elevation=float_or_none(csv_dict_obj["elevation"]),
            distance=float_or_none(csv_dict_obj["distance"]),
            course=float_or_none(csv_dict_obj["course"]),
            speed=float_or_none(csv_dict_obj["speed"]),
            province=csv_dict_obj["province"],
            city=csv_dict_obj["city"],
            area=csv_dict_obj["area"],
            province_en=csv_dict_obj["province_en"],
            city_en=csv_dict_obj["city_en"],
            area_en=csv_dict_obj["area_en"],
            road_num=csv_dict_obj["road_num"],
            road_name=csv_dict_obj["road_name"],
            road_name_en=csv_dict_obj["road_name_en"],
            memo=csv_dict_obj["memo"],
        )


@dataclass
class Route:
    """
    行程
    """
    points: list[RoutePoint]
    """行程中的点"""

    coordinate_type: Optional[str] = None
    """原始类型"""

    transformed_coordinate_type: Optional[str] = None
    """坐标转换后类型"""

    def transform_coordinate(self, force: bool = False):
        """
        转换坐标。转换结果放在 各个点的 longitude_transformed、latitude_transformed
        :param force: 对已经填写转换后坐标的点，是否覆盖内容
        :return: None
        """
        # list(map(lambda point: point.transform_coordinate(coordinate_type, transformed_coordinate_type, force), self.points))
        for point in tqdm(self.points, total=len(self.points), desc="Transform Coordinate", unit='point(s)'):
            point.transform_coordinate(self.coordinate_type, self.transformed_coordinate_type, force)

    def set_area(self, from_nominatim: bool = True, area_gdf_list: list[GeoDataFrame] = None, area_code_conn: sqlite3.Connection = None, force: bool = False):
        """
        填写行政区划。目前的做法是：加载各地区的 geojson 文件（area_gdf_list），判断点属于哪个地区的，得到编码，在给定的 SQLite 文件中找到对应编码的行政区划。
        :param area_gdf_list: 各地区的 geojson 文件转换为 GeoDataFrame 后的列表
        :param area_code_conn: 存放行政区划代码关系的 SQLite 数据库连接
        :param force: 对已经填写地区的点，是否覆盖内容
        :return: None
        """
        # list(map(lambda point: point.set_area(area_gdf_list, area_code_conn, force), self.points))
        for point in tqdm(self.points, total=len(self.points), desc="Set Area", unit='point(s)'):
            point.set_area(from_nominatim=from_nominatim, area_gdf_list=area_gdf_list, area_code_conn=area_code_conn, force=force)

    @staticmethod
    def from_gpx_obj(
            gpx: gpxpy.gpx.GPX, track_index: int = 0, segment_index: int = 0,
            transform_coordinate: bool = False, coordinate_type: str = None, transformed_coordinate_type: str = None,
            set_area: bool = False, from_nominatim: bool = True,
            area_gdf_list: list[GeoDataFrame] = None, area_code_conn: sqlite3.Connection = None
    ) -> 'Route':
        """
        从 GPX 对象导入数据
        :param gpx: GPX 对象
        :param track_index: track 序号
        :param segment_index: segment 序号
        :param transform_coordinate: 是否转换坐标
        :param coordinate_type: 原坐标类型。transform_coordinate == True 时必填
        :param transformed_coordinate_type: 转换后坐标类型。transform_coordinate == True 时必填
        :param set_area: 是否填写行政区划
        :param area_gdf_list: 各地区的 geojson 文件转换为 GeoDataFrame 后的列表。set_area == True 时必填
        :param area_code_conn: 存放行政区划代码关系的 SQLite 数据库连接。set_area == True 时必填
        :return: Route
        """
        if transform_coordinate is True and (coordinate_type is None or transformed_coordinate_type is None):
            raise AttributeError("transform_coordinate is True, but coordinate_type or transformed_coordinate_type is None")
        if set_area is True and (area_gdf_list is None or area_code_conn is None):
            raise AttributeError("set_area is True, but area_gdf_list or area_code_conn is None")
        segment = gpx.tracks[track_index].segments[segment_index]
        first_point = segment.points[0]
        course = 0
        total_distance = 0
        ret_list: list[RoutePoint] = []

        for index, point in tqdm(enumerate(segment.points), total=len(segment.points), desc="Processing GPX Points",
                                 unit='point(s)'):
            if transform_coordinate:
                transformed_coordinate = convert_single_point(point.longitude, point.latitude,
                                                              coordinate_type,
                                                              transformed_coordinate_type)
            else:
                transformed_coordinate = (point.longitude, point.latitude)
            if set_area:
                if from_nominatim:
                    area_info = get_point_info(point.latitude, point.longitude)
                    province_result = area_info['province']
                    city_result = area_info['city']
                    area_result = area_info['area']
                    road_num_result = area_info['road_num']
                    road_name_result = area_info['road_name']
                    province_en_result = area_info['province_en']
                    city_en_result = area_info['city_en']
                    area_en_result = area_info['area_en']
                    road_name_en_result = area_info['road_name_en']
                else:
                    area_info = get_area_info(Point(point.longitude, point.latitude), area_gdf_list=area_gdf_list, area_code_conn=area_code_conn)
                    province_result = area_info[0] if area_info is not None else None
                    city_result = area_info[1] if area_info is not None else None
                    area_result = area_info[2] if area_info is not None else None
                    road_num_result = None
                    road_name_result = None
                    province_en_result = None
                    city_en_result = None
                    area_en_result = None
                    road_name_en_result = None
            else:
                province_result = None
                city_result = None
                area_result = None
                road_num_result = None
                road_name_result = None
                province_en_result = None
                city_en_result = None
                area_en_result = None
                road_name_en_result = None
            if index > 0:
                # distance = calculate_distance(segment.points[index - 1], point)
                prev_point = segment.points[index - 1]
                distance = point.distance_3d(prev_point)
                speed = distance / point.time_difference(prev_point)
                if point.course:
                    course = point.course
                else:
                    course_tmp = calculate_bearing(prev_point, point)
                    if course_tmp != 0:
                        course = course_tmp
                total_distance += distance
            else:
                distance = 0
                speed = 0
                course = 0
            ret_list.append(RoutePoint(
                index=index,
                time=point.time,
                elapsed_time=point.time_difference(first_point),
                longitude=point.longitude,
                latitude=point.latitude,
                longitude_transformed=transformed_coordinate[0],
                latitude_transformed=transformed_coordinate[1],
                elevation=point.elevation,
                distance=total_distance,
                course=course,
                speed=speed,
                province=province_result,
                city=city_result,
                area=area_result,
                road_num=road_num_result,
                road_name=road_name_result,
                province_en=province_en_result,
                city_en=city_en_result,
                area_en=area_en_result,
                road_name_en=road_name_en_result
            ))
        return Route(
            points=ret_list,
            coordinate_type=coordinate_type if transform_coordinate else None,
            transformed_coordinate_type=transformed_coordinate_type if transform_coordinate else None,
        )

    @staticmethod
    def from_gpx_obj_raw(gpx: gpxpy.gpx.GPX, track_index: int = 0, segment_index: int = 0) -> 'Route':
        """
        从 GPX 对象导入数据，但不转换坐标类型，不设置行政区划
        :param gpx: GPX 对象
        :param track_index: track 序号
        :param segment_index: segment 序号
        :return: Route
        """
        return Route.from_gpx_obj(gpx, track_index, segment_index, False, None, None, False, None, None)

    @staticmethod
    def from_gpx_file(
            gpx_file_path: str, track_index: int = 0, segment_index: int = 0,
            transform_coordinate: bool = False, coordinate_type: str = None, transformed_coordinate_type: str = None,
            set_area: bool = False, from_nominatim: bool = True,
            area_gdf_list: list[GeoDataFrame] = None, area_code_conn: sqlite3.Connection = None
    ) -> 'Route':
        """
        从 GPX 文件导入数据
        :param gpx_file_path: GPX 文件路径
        :param track_index: track 序号
        :param segment_index: segment 序号
        :param transform_coordinate: 是否转换坐标
        :param coordinate_type: 原坐标类型。transform_coordinate == True 时必填
        :param transformed_coordinate_type: 转换后坐标类型。transform_coordinate == True 时必填
        :param set_area: 是否填写行政区划
        :param area_gdf_list: 各地区的 geojson 文件转换为 GeoDataFrame 后的列表。set_area == True 时必填
        :param area_code_conn: 存放行政区划代码关系的 SQLite 数据库连接。set_area == True 时必填
        :return: Route
        """
        with open(gpx_file_path, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            return Route.from_gpx_obj(gpx, track_index, segment_index, transform_coordinate, coordinate_type, transformed_coordinate_type, set_area, from_nominatim=from_nominatim, area_gdf_list=area_gdf_list, area_code_conn=area_code_conn)

    @staticmethod
    def from_gpx_file_raw(gpx_file_path: str, track_index: int = 0, segment_index: int = 0) -> 'Route':
        """
        从 GPX 文件导入数据，但不转换坐标类型，不设置行政区划
        :param gpx_file_path: GPX 文件路径
        :param track_index: track 序号
        :param segment_index: segment 序号
        :return: Route
        """
        return Route.from_gpx_file(gpx_file_path, track_index, segment_index, False, None, None, False, False, None, None)

    def to_gpx_obj(self, export_transformed_coordinate: bool = False) -> gpxpy.gpx.GPX:
        """
        导出为 GPX 对象
        :param export_transformed_coordinate: 是否输出转换后的坐标
        :return: gpxpy.gpx.GPX
        """
        gpx = gpxpy.gpx.GPX()
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        for point in self.points:
            if export_transformed_coordinate:
                lat = point.latitude_transformed
                lon = point.longitude_transformed
            else:
                lat = point.latitude
                lon = point.longitude
            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(
                lat, lon,
                elevation=point.elevation,
                time=point.time,
                speed=point.speed
            ))
        gpx_track.segments.append(gpx_segment)
        gpx.tracks.append(gpx_track)
        return gpx

    def to_gpx_file(self, gpx_file_path: str, export_transformed_coordinate: bool = False):
        """
        导出为 GPX 文件
        :param gpx_file_path: GPX 文件路径
        :param export_transformed_coordinate: 是否输出转换后的坐标
        :return: None
        """
        gpx = self.to_gpx_obj(export_transformed_coordinate)
        with open(gpx_file_path, 'w', encoding='utf-8') as f:
            f.write(gpx.to_xml())

    def to_json_dict_obj(self) -> dict[str, Any]:
        """
        转换为能够转为 JSON 字符串的字典类型，供转为 JSON 使用。
        :return: dict[str, Any]
        """
        return {
            'points': [point.to_json_dict_obj() for point in self.points],
            'coordinate_type': self.coordinate_type,
            'transformed_coordinate_type': self.transformed_coordinate_type,
        }

    def to_json(self) -> str:
        """
        转换为 JSON 字符串
        :return: str
        """
        return json.dumps(self.to_json_dict_obj(), ensure_ascii=False)

    def to_json_file(self, json_file_path: str):
        """
        转换为 JSON 文件
        :param json_file_path: JSON 文件路径
        :return: None
        """
        with open(json_file_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

    @staticmethod
    def from_json(json_str: str) -> 'Route':
        """
        从 JSON 字符串导入。该导入方式不会自动转换坐标、填写行政区划
        :param json_str:
        :return: Route
        """
        return Route(
            points = [RoutePoint.from_json_dict_obj(point) for point in json.loads(json_str)['points']],
            coordinate_type = json.loads(json_str)['coordinate_type'],
            transformed_coordinate_type = json.loads(json_str)['transformed_coordinate_type']
        )

    @staticmethod
    def from_json_file(json_file_path: str) -> 'Route':
        """
        从 JSON 文件导入
        :param json_file_path: JSON 文件路径
        :return: Route
        """
        with open(json_file_path, 'r', encoding='utf-8') as f:
            return Route.from_json(f.read())

    def to_csv(self, csv_file_path: str):
        """
        将点转换为 CSV 格式的文件。
        为确保文件能够直接被 Excel 等表格软件打开，指定编码为带 BOM 的 UTF-8
        """
        csv_dict_list = [point.to_csv_dict_obj() for point in self.points]
        csv_util.dict_list_to_csv(csv_dict_list, csv_file_path, encoding='utf-8-sig')

    @staticmethod
    def from_csv(csv_file_path: str, coordinate_type: str = None, transformed_coordinate_type: str = None) -> 'Route':
        """
        从 CSV 文件导入点。因为 CSV 文件不存储坐标类型，故需自行填写。该导入方式不会自动转换坐标、填写行政区划
        :param csv_file_path: CSV 文件路径
        :param coordinate_type: 原坐标类型
        :param transformed_coordinate_type: 转换后坐标类型
        :return: Route
        """
        csv_dict_list = csv_util.csv_to_dict_list(csv_file_path, encoding='utf-8-sig')
        return Route(
            points = [RoutePoint.from_csv_dict_obj(point) for point in csv_dict_list],
            coordinate_type = coordinate_type,
            transformed_coordinate_type = transformed_coordinate_type
        )

if __name__ == '__main__':
    test_route = Route.from_gpx_file(
        # '../../../test/gpx_sample/from_gps_logger.gpx',
        './test/gpx_sample/from_gps_logger.gpx',
        transform_coordinate=True, coordinate_type='wgs84', transformed_coordinate_type='gcj02',
        set_area=True, from_nominatim=True, area_gdf_list=GDFListHandler().list, area_code_conn=AreaCodeConnectHandler().conn
    )
    test_route.to_gpx_file('./test/gpx_sample/from_gps_logger_to_gpx.gpx', export_transformed_coordinate=True)
    test_route_2 = Route.from_gpx_file('./test/gpx_sample/from_gps_logger.gpx',
        transform_coordinate=True, coordinate_type='wgs84', transformed_coordinate_type='gcj02',
        set_area=True, from_nominatim=True, area_gdf_list=GDFListHandler().list, area_code_conn=AreaCodeConnectHandler().conn
    )
    test_route.to_json_file('./test/gpx_sample/from_gps_logger_to_json.json')
    test_route_from_json = Route.from_json_file('./test/gpx_sample/from_gps_logger_to_json.json')
    test_route.to_csv('./test/gpx_sample/from_gps_logger_to_csv.csv')
    test_route_from_csv = Route.from_csv('./test/gpx_sample/from_gps_logger_to_csv.csv', coordinate_type='wgs84', transformed_coordinate_type='gcj02')
    print(test_route.points[0])
    print(test_route_from_json.points[0])
    print(test_route_from_csv.points[0])
