import time

import requests
from loguru import logger

from src.gpxutil.core.config import CONFIG_HANDLER



def reverse_geocoding(lon, lat, lang: str='zh-CN'):
    """
    百度逆向编码
    :param lon: 经度
    :param lat: 纬度
    :return:
    """
    url = 'https://api.map.baidu.com/reverse_geocoding/v3/'
    params = {
        'ak': CONFIG_HANDLER.config.area_info.baidu.ak,
        # 'extensions_poi': 1,
        # 'entire_poi': 1,
        'sort_strategy': 'distance',
        'output': 'json',
        'coordtype': 'wgs84ll',
        'location': f'{lat},{lon}',
        'poi_types': '道路',
        'language': lang
    }
    time.sleep(1/CONFIG_HANDLER.config.area_info.baidu.freq)
    response = requests.get(url, params=params)
    return response.json()

def get_point_info(lat, lon):
    province, city, area, town, road_name, road_num, province_en, city_en, area_en, town_en, road_name_en, road_num_en, memo = '', '', '', '', '', '', '', '', '', '', '', '', ''
    resp = reverse_geocoding(lon, lat)
    if resp['status'] == 0:
        province = resp['result']['addressComponent']['province']
        city = resp['result']['addressComponent']['city']
        area = resp['result']['addressComponent']['district']
        town = resp['result']['addressComponent']['town']
        road_name = resp['result']['addressComponent']['street']
        if road_name == '':
            roads = resp['result']['business_info']
            if roads:
                min_distance = min(roads, key=lambda x: x['distance'])['distance']
                nearest_roads = [road for road in roads if road['distance'] == min_distance]
                if nearest_roads:
                    road_name = ', '.join([road['name'] for road in nearest_roads if road['name']])
    else:
        logger.error(f'百度逆向编码错误: {resp}')
    if CONFIG_HANDLER.config.area_info.baidu.get_en_result:
        resp_en = reverse_geocoding(lon, lat, 'en')
        if resp_en['status'] == 0:
            province_en = resp_en['result']['addressComponent']['province']
            city_en = resp_en['result']['addressComponent']['city']
            area_en = resp_en['result']['addressComponent']['district']
            town_en = resp_en['result']['addressComponent']['town']
            road_name_en = resp['result']['addressComponent']['street']
            if road_name_en == '':
                roads = resp['result']['business_info']
                if roads:
                    min_distance = min(roads, key=lambda x: x['distance'])['distance']
                    nearest_roads = [road for road in roads if road['distance'] == min_distance]
                    if nearest_roads:
                        road_name_en = ', '.join([road['name'] for road in nearest_roads if road['name']])
            if province_en ==  province:
                province_en = ''
            if city_en == city:
                city_en = ''
            if area_en == area:
                area_en = ''
            if town_en == town:
                town_en = ''
            if  road_name_en == road_name:
                road_name_en = ''
        else:
            logger.error(f'百度逆向编码错误: {resp_en}')
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
