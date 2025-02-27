import csv
import math
import os
import sqlite3
from datetime import datetime
from typing import List

import geopandas as gpd
import gpxpy.gpx
from geopandas import GeoDataFrame
from shapely.geometry import Point

from tqdm import tqdm


# 计算方位角
def calculate_bearing(point1, point2):
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

def load_area_gdf_list(geojson_dir: str) -> List[GeoDataFrame]:
    gdf_list = []
    # 读取目录里所有文件
    filename_list = os.listdir(geojson_dir)
    for filename in tqdm(filename_list, total=len(filename_list), desc="Load Area GeoJSON files", unit='file(s)'):
        if filename.endswith(".json") or filename.endswith(".geojson"):
            gdf_list.append(gpd.read_file(os.path.join(geojson_dir, filename)))
    return gdf_list

def get_area_id(point: Point, area_gdf_list: List[GeoDataFrame]) -> str:
    for i, gdf in enumerate(area_gdf_list):
        for index, row in gdf.iterrows():
            polygon = row['geometry']  # 获取多边形
            if polygon.contains(point):  # 判断点是否在多边形内
                # print(f"点 ({point.x}, {point.y}) 在区域 {row['id']} 中，区域名称为 {row['name']}")
                return row['id']
    raise ValueError(f"点 ({point.x}, {point.y}) 不在任何已知区域内")

def get_area_info(point: Point, area_gdf_list: List[GeoDataFrame], area_code_conn: sqlite3.Connection):
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

def segment_to_dict_list(segment: gpxpy.gpx.GPXTrackSegment, area_gdf_list: List[GeoDataFrame], area_code_conn: sqlite3.Connection) -> List[dict]:
    first_point = segment.points[0]
    course = 0
    total_distance = 0
    ret_list: List[dict] = []

    for index, point in tqdm(enumerate(segment.points), total=len(segment.points), desc="Processing GPX Points", unit='point(s)'):
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
        # print(index, point.time_difference(first_point), point.longitude, point.latitude, point.elevation,
        #       total_distance, course, speed * 3600 / 1000)
        area_info = get_area_info(Point(point.longitude, point.latitude), area_gdf_list, area_code_conn)
        ret_list.append({
            'index': index,
            'time': point.time,
            # 'time_iso': point.time.isoformat(),
            'elapsed_time': point.time_difference(first_point),
            'longitude': point.longitude,
            'latitude': point.latitude,
            'elevation': point.elevation,
            'distance': total_distance,
            'course': course,
            'speed': speed,
            'province': area_info[0],
            'city': area_info[1],
            'area': area_info[2],
        })
    return ret_list

def single_segment_gpx_to_dict_list(gpx: gpxpy.gpx.GPX, area_gdf_list: List[GeoDataFrame], area_code_conn: sqlite3.Connection) -> List[dict]:
    return segment_to_dict_list(gpx.tracks[0].segments[0], area_gdf_list, area_code_conn)

def single_segment_gpx_file_path_to_dict_list(gpx_file_path: str, area_gdf_list: List[GeoDataFrame], area_code_conn: sqlite3.Connection) -> List[dict]:
    with open(gpx_file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
        return single_segment_gpx_to_dict_list(gpx, area_gdf_list, area_code_conn)

def dict_list_to_csv(dict_list: List[dict], csv_file_path: str):
    fieldnames = dict_list[0].keys()

    # 打开 CSV 文件并写入数据
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        # 写入表头
        writer.writeheader()

        # 写入数据行
        for row_dict in dict_list:
            write_row = row_dict.copy()
            if 'time' in write_row and write_row['time']:
                write_row['time'] = write_row['time'].astimezone(datetime.now().tzinfo).strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow(write_row)

def single_segment_gpx_file_path_to_csv(gpx_file_path: str, csv_file_path: str, area_gdf_list: List[GeoDataFrame], area_code_conn: sqlite3.Connection):
    dict_list = single_segment_gpx_file_path_to_dict_list(gpx_file_path, area_gdf_list, area_code_conn)
    dict_list_to_csv(dict_list, csv_file_path)

if __name__ == '__main__':
    gdf_list = load_area_gdf_list(r"asset\area_geojson")
    conn = sqlite3.connect(r"asset\area_code.sqlite")
    single_segment_gpx_file_path_to_csv('test/20250226132250.gpx', 'test/20250226132250-2.csv', gdf_list, conn)