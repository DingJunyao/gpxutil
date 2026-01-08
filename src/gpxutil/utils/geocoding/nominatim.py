import requests
from loguru import logger

from src.gpxutil.core.config import CONFIG_HANDLER


def reverse(lat, lon, accept_language: str = 'zh-CN', host: str = None):
    host = host or CONFIG_HANDLER.config.area_info.nominatim.url
    url = host + '/reverse'
    params = {
        'lat': lat,
        'lon': lon,
        'format': 'geocodejson',
        'layer': 'address',
        'extratags': 1,
        'zoom': 17,
        'accept-language': accept_language
    }
    return requests.get(url, params=params).json()

def search(query, host: str = None):
    host = host or CONFIG_HANDLER.config.area_info.nominatim.url
    url = host + '/search'
    params = {
        'q': query,
        'addressdetails': 1,
    }
    return requests.get(url, params=params).json()

def details(place_id, host: str = None):
    host = host or CONFIG_HANDLER.config.area_info.nominatim.url
    url = host + '/details'
    params = {
        'place_id': place_id,
    }
    return requests.get(url, params=params).json()

def get_point_info(lat, lon, host: str = None):
    host = host or CONFIG_HANDLER.config.area_info.nominatim.url
    province, city, area, town, road_name, road_num, province_en, city_en, area_en, town_en, road_name_en, road_num_en, memo = '', '', '', '', '', '', '', '', '', '', '', '', ''
    try:
        rev = reverse(lat, lon, host=host)
        rev_en = reverse(lat, lon, 'en', host=host)
        admin_dict = rev['features'][0]['properties']['geocoding']['admin']
        admin_dict_en = rev_en['features'][0]['properties']['geocoding']['admin']
        province = admin_dict.get('level4', '')
        city = admin_dict.get('level5', '')
        area = admin_dict.get('level6', '')
        town = admin_dict.get('level8', '')
        province_en = admin_dict_en.get('level4', '')
        city_en = admin_dict_en.get('level5', '')
        area_en = admin_dict_en.get('level6', '')
        town_en = admin_dict_en.get('level8', '')
        if rev['features'][0]['properties']['geocoding']['osm_type'] == 'way':
            road_name = rev['features'][0]['properties']['geocoding']['name']
            road_name_en = rev_en['features'][0]['properties']['geocoding']['name']
            if road_name_en == road_name:
                road_name_en = ''
            road_detail = details(rev['features'][0]['properties']['geocoding']['place_id'])
            if 'ref' in road_detail['names']:
                road_num = ','.join(road_detail['names']['ref'].split(';'))
    except Exception as e:
        logger.warning('Some info of (%s, %s) is empty. API response: %s' % (lat, lon, rev['features'][0]['properties']['geocoding']))
        memo = str(e)
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
    lat = 30.44094238
    lon = 114.61355524
    print(get_point_info(lat, lon))
