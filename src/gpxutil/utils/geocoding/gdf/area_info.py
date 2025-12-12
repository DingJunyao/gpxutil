import sqlite3
from typing import List

from geopandas import GeoDataFrame
from shapely import Point

from src.gpxutil.models.exceptions import PointAreaNotFoundException


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
    raise PointAreaNotFoundException(f"点 ({point.x}, {point.y}) 不在任何已知区域内")


def get_area_info(point: Point, area_gdf_list: List[GeoDataFrame], area_code_conn: sqlite3.Connection):
    """
    获取给定点所在地区的行政区划信息。
    :param point: 点
    :param area_gdf_list: 各地区的 geojson 文件转换为 GeoDataFrame 后的列表
    :param area_code_conn: 存放行政区划代码关系的 SQLite 数据库连接
    :return: 省级、市级、县级行政区划名称
    """
    cursor = area_code_conn.cursor()
    try:
        area_id = get_area_id(point, area_gdf_list)
    except PointAreaNotFoundException:
        return None, None, None
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
