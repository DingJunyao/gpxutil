from ast import main
import csv
from dataclasses import dataclass
from datetime import datetime

from tqdm import tqdm

NATIONAL_HIGHWAY_TEMPLATE = "{% label {{code}} red %}"
PROVINCIAL_HIGHWAY_TEMPLATE = "{% label {{code}} orange %}"
OTHER_HIGHWAY_TEMPLATE = "{% label {{code}} white %}"
EXPWY_TEMPLATE = "{% label {{code}} green %}"
CITY_TIMELINE_TEMPLATE = """{% timeline {{province}} {{city}}（视频 XX:XX） %}
{{areas_info}}
{% endtimeline %}"""
AREA_TIMELINE_TEMPLATE = """<!-- timeline {{area}}（视频 XX:XX） -->
{{road_info}}
<!-- endtimeline -->"""

# @dataclass
# class AreaRoadInfo:
#     province: str
#     city: str
#     area: str
#     road_code: list[str]
#     road_name: str
    
#     def area_eq(self, other):
#          return self.province == other.province and self.city == other.city and self.area == other.area
     
#     def road_eq(self, other):
#          return self.road_code == other.road_code and self.road_name == other.road_name
     
#     def __eq__(self, other):
#         return self.area_eq(other) and self.road_eq(other)
    
#     def __str__(self):
#         return f'AreaRoadInfo({self.province} {self.city} {self.area}, {self.road_code}: {self.road_name})'
    
#     __repr__ = __str__
    
@dataclass
class RoadInfo:
    code: list[str]
    name: str
    
    def __eq__(self, value):
        return self.code == value.code and self.name == value.name
    def __str__(self):
        return f'RoadInfo({self.code}: {self.name})'
    
    __repr__ = __str__

@dataclass
class AreaInfo:
    name: str
    roads: list[RoadInfo]
    
    def __eq__(self, value):
        return  self.name == value.name
    
    def __str__(self):
        return f'AreaInfo({self.name} \n \t\t > {self.roads})'
    
    __repr__ = __str__

@dataclass
class CityInfo:
    province: str
    city: str
    areas: list[AreaInfo]
    def __str__(self):
        return f'CityInfo({self.province} {self.city})'
    
    def __eq__(self, value):
        return self.province == value.province and self.city == value.city
    
    def __str__(self):
        return  f'CityInfo({self.province} {self.city} \n \t > {self.areas})'
    
    __repr__ = __str__





def read_csv(path: str) -> list[dict]:
    dict_list = []
    with open(path, mode='r', newline='', encoding='utf-8-sig') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in tqdm(reader, desc='Processing csv data', unit='point(s)'):
            dict_list.append(row)
            for key, value in row.items():
                if value == '':
                    row[key] = None
                elif key == 'time':
                    row[key] = datetime.strptime(
                        value,
                        # '%Y-%m-%d %H:%M:%S'
                        '%Y/%m/%d %H:%M:%S'
                    )
                elif key == 'elapsed_time':
                    row[key] = int(float(value))
                elif key in ['latitude', 'longitude', 'elevation', 'distance', 'course', 'speed']:
                    row[key] = float(value)
                else:
                    row[key] = value
        return dict_list
    

def get_info(csv_dict_list: list[dict]):
    # area_info_list = []
    # for csv_dict in tqdm(csv_dict_list, desc='Getting area info', unit='point(s)'):
    #     area_info = AreaRoadInfo(
    #         province=csv_dict['province'],
    #         city=csv_dict['city'],
    #         area=csv_dict['area'],
    #         road_code=csv_dict['road_num'].split(',') if csv_dict['road_num'] else [],
    #         road_name=csv_dict['road_name'],
    #     )
    #     if len(area_info_list) >= 1 and area_info_list[-1]  == area_info:
    #         continue
    #     area_info_list.append(area_info)
    # return area_info_list
    city_info_list: list[CityInfo] = []
    for csv_dict in tqdm(csv_dict_list, desc='Getting area info', unit='point(s)'):
        city_info = CityInfo(
            province=csv_dict['province'],
            city=csv_dict['city'],
            areas=[AreaInfo(
                name=csv_dict['area'],
                roads=[RoadInfo(
                    code=csv_dict['road_num'].split(',') if csv_dict['road_num'] else [],
                    name=csv_dict['road_name'],
               )]
            )]
        )
        if len(city_info_list) >= 1 and city_info_list[-1]  == city_info:
            last_city_info = city_info_list[-1]
            if last_city_info.areas[-1] == city_info.areas[-1]:
                last_road_info = last_city_info.areas[-1].roads[-1]
                if last_road_info == city_info.areas[-1].roads[-1]:
                    continue
                else:
                     city_info_list[-1].areas[-1].roads.extend(city_info.areas[-1].roads)
            else:
                city_info_list[-1].areas.extend(city_info.areas)
        else:
            city_info_list.append(city_info)
    return city_info_list


def gen_single_road_code(road_code: str) -> str:
    # G1 G11 G111 G1111 京S1 京S11 京S111 京S1111 S111 X111 Y111
    if not road_code:
        return ""
    if road_code[0] not in 'GSXYQT':
        province = road_code[0] + " "
        road_code = road_code[1:]
    else:
        province = ""
    if len(road_code) == 4:
        if road_code.startswith('G'):
            return NATIONAL_HIGHWAY_TEMPLATE.replace('{{code}}', road_code)
        elif road_code.startswith('S'):
            return province + PROVINCIAL_HIGHWAY_TEMPLATE.replace('{{code}}', road_code)
        else:
            return OTHER_HIGHWAY_TEMPLATE.replace('{{code}}', road_code)
    elif len(road_code) == 5:
            return province + EXPWY_TEMPLATE.replace('{{code}}', f"{road_code[:-2]}<sub>{road_code[-2:]}</sub>")
    else:
        return province + EXPWY_TEMPLATE.replace('{{code}}', road_code)

def gen_single_road_info(road: RoadInfo):
    if not road.code and not road.name:
        return ""
    return ' / '.join([gen_single_road_code(code) for code in road.code]) + (" " if road.code else "") + (road.name if road.name else "")

def merge_itrchg_and_toll_station(in_list):
    """处理立交和收费站的合并事宜。列表中如果有“互通”“立交”“枢纽”和“收费站”结尾的项目相连，则合并为 “XX互通/立交/枢纽（XXX收费站）
    """
    hint_words = ["互通", "立交", "枢纽"]  # 指示词后缀
    toll_suffix = "收费站"  # 收费站后缀
    result = []  # 存储处理结果
    i = 0  # 列表索引
    
    while i < len(in_list):
        # 检查是否到达最后一个元素
        if i == len(in_list) - 1:
            result.append(in_list[i])
            break
        
        current = in_list[i]
        next_item = in_list[i+1]
        
        # 检查是否应该合并
        should_merge = False
        merged = ""
        
        # 情况1：当前是指示词，下一个是收费站
        if any(current.endswith(word) for word in hint_words) and next_item.endswith(toll_suffix):
            merged = f"{current}（{next_item}）"
            should_merge = True
        
        # 情况2：当前是收费站，下一个是指示词
        elif current.endswith(toll_suffix) and any(next_item.endswith(word) for word in hint_words):
            merged = f"{next_item}（{current}）"
            should_merge = True
        
        # 执行合并或添加单独项
        if should_merge:
            result.append(merged)
            i += 2  # 跳过两个元素
        else:
            result.append(current)
            i += 1  # 移动到下一个元素
    
    return result

def merge_empty_items(in_list):
    """
    处理空白值：如果空字符串前后项的值相等，则合并这三项（保留一个非空值）
    """
    changed = True
    lst = in_list[:]  # 创建列表副本
    
    # 循环处理直到没有变化发生
    while changed:
        changed = False
        new_lst = []
        i = 0
        n = len(lst)
        
        while i < n:
            # 检查空字符串且满足合并条件
            if lst[i] == '' and new_lst and i + 1 < n and new_lst[-1] == lst[i + 1]:
                # 跳过空字符串和下一个元素
                i += 2
                changed = True
            else:
                # 非空元素加入新列表
                if lst[i] != '':
                    new_lst.append(lst[i])
                i += 1
        
        lst = new_lst  # 更新列表进行下一轮处理
    
    return lst

def gen_route_info(city_info_list: list[CityInfo]) -> str:
    """根据 CSV 文件生成途经信息，输出结果如下：
    {% timeline  江西省 九江市（视频 XX:XX） %}

    <!-- timeline 浔阳区（视频 XX:XX） -->
    滨江路 → 龙开河路 → 北径路 → 三马路 → {% label G351 red %} 浔阳西路 → 三马路 → 北径路 → 龙开河路 → 滨江路 → 滨江东路…
    <!-- endtimeline -->
    <!-- timeline 濂溪区（视频 XX:XX） -->
    …滨江东路 → {% label S306 orange %} 滨江东路 → {% label S306 orange %} 九湖路 → {% label S306 orange %}  → {% label S306 orange %} 梅家洲渡口 → {% label S306 orange %}  → {% label S306 orange %} 九湖路 → {% label S306 orange %} 滨江东路 → 洪垅大道 → {% label X175 white %} 洪垅大道 → {% label S306 orange %} / {% label X175 white %} 九湖路 → 芳兰大道 → 九湖路 → {% label X175 white %} 九湖路 → {% label G351 red %} / {% label X175 white %} 九湖路…
    <!-- endtimeline -->
    <!-- timeline 浔阳区（视频 XX:XX） -->
    …{% label G351 red %} / {% label X175 white %} 九湖路…
    <!-- endtimeline -->
    <!-- timeline 濂溪区（视频 XX:XX） -->
    …{% label G351 red %} / {% label X175 white %} 九湖路 → 琴湖大道 → 琴湖大道互通 → 昌九快速路 → 九江东收费站 → 赣 {% label S22 green %} 都九高速…
    <!-- endtimeline -->
    <!-- timeline 湖口县（视频 XX:XX） -->
    …赣 {% label S22 green %} 都九高速 → 石钟山服务区 → 赣 {% label S22 green %} 都九高速…
    <!-- endtimeline -->
    <!-- timeline 都昌县（视频 XX:XX） -->
    …赣 {% label S22 green %} 都九高速 → {% label G56 green %} / 赣 {% label S22 green %} 杭瑞高速 → {% label G56 green %} 杭瑞高速…
    <!-- endtimeline -->
    {% endtimeline %}
    {% timeline  江西省 上饶市（视频 XX:XX） %}

    <!-- timeline 鄱阳县（视频 XX:XX） -->
    …{% label G56 green %} 杭瑞高速…
    <!-- endtimeline -->
    {% endtimeline %}
    {% timeline  江西省 景德镇市（视频 XX:XX） %}

    <!-- timeline 浮梁县（视频 XX:XX） -->
    …{% label G56 green %} 杭瑞高速 → 景德镇西互通（景德镇西收费站） → 迎宾大道…
    <!-- endtimeline -->
    <!-- timeline 昌江区（视频 XX:XX） -->
    …迎宾大道 → {% label G351 red %} 迎宾大道 → 新平路 → 珠山大道 → {% label S308 orange %} 珠山大道…
    <!-- endtimeline -->
    <!-- timeline 珠山区（视频 XX:XX） -->
    …{% label S308 orange %} 珠山大道 → 中华南路 → 麻石上弄 → 中山南路 → 麻石上弄 → 中华南路 → {% label S308 orange %} 珠山大道 → 莲社南路
    <!-- endtimeline -->
    {% endtimeline %}
    """
    city_name_list = []
    city_area_name_list = []
    city_timeline_text = ''
    city_road_list = []
    for city_i, city in enumerate(city_info_list):
        area_timeline_text = ''
        area_road_list = []
        for area_i, area in enumerate(city.areas):
            road_text_list = [gen_single_road_info(road) for road in area.roads]
            road_text_list = merge_itrchg_and_toll_station(road_text_list)
            road_text_list = merge_empty_items(road_text_list)
            # 如果 road_text_list 第一项与它的前一个路相同，则给两边加上省略号
            # 找到前一个路    
            if city_i != 0 or area_i != 0:
                # 否则没有前一个路
                if area_i == 0:
                    # 前一个路在上一个市里面
                    if road_text_list[0].replace('…', '') == city_road_list[-1][-1][-1].replace('…', ''):
                        road_text_list[0] = '…' + road_text_list[0]
                        city_road_list[-1][-1][-1] = city_road_list[-1][-1][-1] + '…'
                else:
                    # 前一个路在上一个区里面，注意此时还没有入 city_list
                    if road_text_list[0].replace('…', '') == area_road_list[-1][-1].replace('…', ''):
                        road_text_list[0] = '…' + road_text_list[0]
                        area_road_list[-1][-1] = area_road_list[-1][-1] + '…'
            area_road_list.append(road_text_list)
            area_timeline_text += '\n' + AREA_TIMELINE_TEMPLATE.replace('{{area}}', area.name)
        city_road_list.append(area_road_list)
        city_timeline_text += '\n' + CITY_TIMELINE_TEMPLATE.replace('{{province}}', city.province).replace('{{city}}', city.city).replace('{{areas_info}}', area_timeline_text)
    for city_roads in city_road_list:
        for area_roads in city_roads:
            city_timeline_text = city_timeline_text.replace('{{road_info}}', ' → '.join(area_roads), 1)
    return city_timeline_text


if __name__ == '__main__':
    csv_dict_list = read_csv(r'E:\project\recorded\route\gcj\九江.csv')
    city_info_list = get_info(csv_dict_list)
    print(gen_route_info(city_info_list))
    # for city in get_info(csv_dict_list):
    #     print(city.province, city.city)
    #     for area in city.areas:
    #         print('\t > ', area.name)
    #         for road in area.roads:
    #             print('\t\t > ', gen_single_road_info(road))