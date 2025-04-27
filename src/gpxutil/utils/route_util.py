import math
import sqlite3
from typing import List

import gpxpy.gpx
from geopandas import GeoDataFrame
from shapely import Point


def calculate_bearing(point1: gpxpy.gpx.GPXTrackPoint, point2: gpxpy.gpx.GPXTrackPoint):
    """
    计算方位角。
    :param point1: 起始点
    :param point2: 结束点
    :return:
    """
    lat1, lon1 = point1.latitude, point1.longitude
    lat2, lon2 = point2.latitude, point2.longitude

    dlon = lon2 - lon1
    x = math.cos(math.radians(lat2)) * math.sin(math.radians(dlon))
    y = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(math.radians(lat1)) * math.cos(
        math.radians(lat2)) * math.cos(math.radians(dlon))
    bearing = math.atan2(x, y)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    return bearing


def get_area_id(point: Point, area_gdf_list: List[GeoDataFrame]) -> str:
    """
    获取给定点所在地区的行政区划代码。
    :param point: 点
    :param area_gdf_list: 各地区的 geojson 文件转换为 GeoDataFrame 后的列表
    :return:
    """
    for i, gdf in enumerate(area_gdf_list):
        for index, row in gdf.iterrows():
            polygon = row['geometry']  # 获取多边形
            if polygon.contains(point):  # 判断点是否在多边形内
                # print(f"点 ({point.x}, {point.y}) 在区域 {row['id']} 中，区域名称为 {row['name']}")
                return row['id']
    raise ValueError(f"点 ({point.x}, {point.y}) 不在任何已知区域内")


def get_area_info(point: Point, area_gdf_list: List[GeoDataFrame], area_code_conn: sqlite3.Connection):
    """
    获取给定点所在地区的行政区划信息。
    :param point: 点
    :param area_gdf_list: 各地区的 geojson 文件转换为 GeoDataFrame 后的列表
    :param area_code_conn: 存放行政区划代码关系的 SQLite 数据库连接
    :return: 省级、市级、县级行政区划名称
    """
    cursor = area_code_conn.cursor()
    area_id = get_area_id(point, area_gdf_list)
    sql = """
    select province.name, city.name, area.name
    from province, city, area
    where
        province.code = area.provinceCode
        and city.code = area.cityCode
        and area.code = ?
    """
    cursor.execute(sql, (area_id,))
    result = cursor.fetchone()
    cursor.close()
    return result
