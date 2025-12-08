import time

import requests
from loguru import logger

from src.gpxutil.core.config import CONFIG_HANDLER
from src.gpxutil.utils.gpx_convert import convert_single_point


def reverse_geocoding(lon, lat):
    """
    高德逆向编码
    :param lon: 经度
    :param lat: 纬度
    :return:
    """
    url = 'https://restapi.amap.com/v3/geocode/regeo'
    trans_lon, trans_lat = convert_single_point(lon, lat, 'wgs84', 'gcj02')
    params = {
        'key': CONFIG_HANDLER.config.area_info.amap.ak,
        'location': f'{trans_lon},{trans_lat}',
        'poitype': 180000,
        'radius': 500,
        'extensions': 'all',
    }
    time.sleep(1/CONFIG_HANDLER.config.area_info.amap.freq)
    response = requests.get(url, params=params)
    return response.json()

def get_point_info(lat, lon):
    province, city, area, town, road_name, road_num, province_en, city_en, area_en, town_en, road_name_en, road_num_en, memo = '', '', '', '', '', '', '', '', '', '', '', '', ''
    resp = reverse_geocoding(lon, lat)
    if resp['status'] == "1" and resp['infocode'] == "10000":
        province = resp['regeocode']['addressComponent']['province']
        city = resp['regeocode']['addressComponent']['city']
        area = resp['regeocode']['addressComponent']['district']
        town = resp['regeocode']['addressComponent']['township']
        # 1
        if 'streetNumber' in resp['regeocode']['addressComponent'] and resp['regeocode']['addressComponent']['streetNumber']:
            if isinstance(resp['regeocode']['addressComponent']['streetNumber']['street'], list):
                road_name = ','.join(resp['regeocode']['addressComponent']['streetNumber']['street'])
            else:
                road_name = resp['regeocode']['addressComponent']['streetNumber']['street']
        # 2
        if road_name == '':
            roads = resp['regeocode']['roads']
            if roads:
                min_distance = min(roads, key=lambda x: x['distance'])['distance']
                nearest_roads = [road for road in roads if road['distance'] == min_distance]
                if nearest_roads:
                    road_name = ', '.join([road['name'] for road in nearest_roads if road['name']])
    else:
        logger.error(f'高德逆向编码错误: {resp}')
    return {
        'province': province,
        'city': city,
        'area': area,
        'town': town,
        'road_name': road_name,
        'road_num': road_num,
        'province_en': province_en,
        'city_en': city_en,
        'area_en': area_en,
        'town_en': town_en,
        'road_name_en': road_name_en,
        'memo': memo
    }


if __name__ == '__main__':
    lat = 30.49117517
    lon = 114.49190074
    print(get_point_info(lat, lon))
