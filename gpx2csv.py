import csv
import math
from typing import List

import gpxpy.gpx

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

def segment_to_dict_list(segment: gpxpy.gpx.GPXTrackSegment) -> List[dict]:
    first_point = segment.points[0]
    course = 0
    total_distance = 0
    ret_list: List[dict] = []

    for index, point in enumerate(segment.points):
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
        ret_list.append({
            'index': index,
            'time': point.time,
            'elapsed_time': point.time_difference(first_point),
            'longitude': point.longitude,
            'latitude': point.latitude,
            'elevation': point.elevation,
            'distance': total_distance,
            'course': course,
            'speed': speed
        })
    return ret_list

def single_segment_gpx_to_dict_list(gpx: gpxpy.gpx.GPX) -> List[dict]:
    return segment_to_dict_list(gpx.tracks[0].segments[0])

def single_segment_gpx_file_path_to_dict_list(gpx_file_path: str) -> List[dict]:
    with open(gpx_file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
        return single_segment_gpx_to_dict_list(gpx)

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
            write_row['time'] = write_row['time'].strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow(write_row)

def single_segment_gpx_file_path_to_csv(gpx_file_path: str, csv_file_path: str):
    dict_list = single_segment_gpx_file_path_to_dict_list(gpx_file_path)
    dict_list_to_csv(dict_list, csv_file_path)

if __name__ == '__main__':
    single_segment_gpx_file_path_to_csv('test/test.gpx', 'test/test_self.csv')