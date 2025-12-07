import requests

HOST = 'http://localhost:8080'

def reverse(lat, lon, accept_language: str = 'zh-CN'):
    url = HOST + '/reverse'
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

def search(query):
    url = HOST + '/search'
    params = {
        'q': query,
        'addressdetails': 1,
    }
    return requests.get(url, params=params).json()

def details(place_id):
    url = HOST + '/details'
    params = {
        'place_id': place_id,
    }
    return requests.get(url, params=params).json()

def get_point_info(lat, lon):
    province, city, area, town, road_name, road_num, province_en, city_en, area_en, town_en, road_name_en, road_num_en, memo = '', '', '', '', '', '', '', '', '', '', '', '', ''
    try:
        rev = reverse(lat, lon)
        rev_en = reverse(lat, lon, 'en')
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
                road_num = road_detail['names']['ref']
    except Exception as e:
        print(lat, lon, rev['features'][0]['properties']['geocoding'])
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
    lat = 30.49117517
    lon = 114.49190074
    print(get_point_info(lat, lon))
