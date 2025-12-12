import math

import gpxpy.gpx


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
