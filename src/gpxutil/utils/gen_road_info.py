from ast import main
import csv
from dataclasses import dataclass, field
from datetime import datetime

from tqdm import tqdm

from src.gpxutil.models.indonesia import IndonesiaRoadLevel, parse_indonesia_road_num
from src.gpxutil.models.region import Region, get_default_languages, get_field_suffix

NATIONAL_HIGHWAY_TEMPLATE = "{% label {{code}} red %}"
PROVINCIAL_HIGHWAY_TEMPLATE = "{% label {{code}} orange %}"
OTHER_HIGHWAY_TEMPLATE = "{% label {{code}} white %}"
EXPWY_TEMPLATE = "{% label {{code}} green %}"

# timeline 副语言行前缀：主语言 zh 无前缀，副语言逐行对照
LANG_PREFIX = {'zh': '', 'id': '印尼语：', 'en': '英语：'}

# 印尼 label 等级颜色。注意：label 层无路名（tol 关键词不可见），
# 1-2 位编号一律按 NASIONAL(red) 输出；等级->颜色映射保留以便后续按 RoadInfo 等级增强
INDONESIA_LABEL_COLOR = {
    IndonesiaRoadLevel.NASIONAL: 'red',
    IndonesiaRoadLevel.TOL: 'green',
    IndonesiaRoadLevel.PROVINSI: 'blue',
}

CITY_TIMELINE_TEMPLATE = """{% timeline {{province}} {{city}}（视频 XX:XX） %}
{{city_secondary}}{{areas_info}}
{% endtimeline %}"""
AREA_TIMELINE_TEMPLATE = """<!-- timeline {{area}}（视频 XX:XX） -->
{{area_secondary}}{{road_info}}
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
    names: dict[str, str]  # 语言 -> 路名（键为主语言 zh 与各副语言）

    def __eq__(self, value):
        # 沿用主语言（zh）名比较，与旧单语言行为一致
        return self.code == value.code and self.names.get('zh', '') == value.names.get('zh', '')

    def __str__(self):
        return f'RoadInfo({self.code}: {self.names.get("zh", "")})'

    __repr__ = __str__


@dataclass
class AreaInfo:
    names: dict[str, str]  # 语言 -> 区名
    roads: list[RoadInfo]

    def __eq__(self, value):
        return self.names.get('zh', '') == value.names.get('zh', '')

    def __str__(self):
        return f'AreaInfo({self.names.get("zh", "")} \n \t\t > {self.roads})'

    __repr__ = __str__


@dataclass
class CityInfo:
    province: str  # 主语言（zh）省名，模板占位符 {{province}}
    city: str      # 主语言（zh）城市名，模板占位符 {{city}}
    areas: list[AreaInfo]
    # 语言 -> (省名, 城市名)，供 timeline 副语言对照行使用
    names: dict[str, tuple[str, str]] = field(default_factory=dict)

    def __eq__(self, value):
        return self.province == value.province and self.city == value.city

    def __str__(self):
        return f'CityInfo({self.province} {self.city} \n \t > {self.areas})'

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
    

def get_info(csv_input, region: Region = Region.CN):
    """从 CSV 行列表或 CSV 文件路径构建层级信息列表

    :param csv_input: read_csv 的 dict 列表，或 CSV 文件路径（内部自行 read_csv）
    :param region: 地区，决定语言集与 CSV 字段后缀（主语言 zh + 副语言）
    :return: list[CityInfo]
    """
    if isinstance(csv_input, str):
        csv_dict_list = read_csv(csv_input)
    else:
        csv_dict_list = csv_input
    primary, secondary = get_default_languages(region)
    langs = [primary] + secondary
    city_info_list: list[CityInfo] = []
    for csv_dict in tqdm(csv_dict_list, desc='Getting area info', unit='point(s)'):
        city_info = CityInfo(
            province=csv_dict['province'] if csv_dict['province'] else '',
            city=csv_dict['city'] if csv_dict['city'] else '',
            names={lang: (csv_dict.get(f'province{get_field_suffix(lang)}') or '',
                          csv_dict.get(f'city{get_field_suffix(lang)}') or '')
                   for lang in langs},
            areas=[AreaInfo(
                names={lang: csv_dict.get(f'area{get_field_suffix(lang)}') or '' for lang in langs},
                roads=[RoadInfo(
                    code=csv_dict['road_num'].split(',') if csv_dict['road_num'] else [],
                    names={lang: csv_dict.get(f'road_name{get_field_suffix(lang)}') or '' for lang in langs},
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


def gen_single_road_code(road_code: str, region: Region = Region.CN) -> str:
    if not road_code:
        return ""
    if region == Region.ID:
        # 印尼：1-2 位 = NASIONAL（可能 TOL，需路名关键词，label 层不可见），3 位 = PROVINSI
        info = parse_indonesia_road_num(road_code, None, [], [])
        if info is None:
            return ""
        return f"{{% label {info.code} {INDONESIA_LABEL_COLOR[info.level]} %}}"
    # G1 G11 G111 G1111 京S1 京S11 京S111 京S1111 S111 X111 Y111
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

def gen_single_road_info(road: RoadInfo, region: Region = Region.CN) -> str:
    """道路主行（label + 主语言路名），副语言路名以两个空格缩进逐行附加"""
    primary, secondary = get_default_languages(region)
    if not road.code and not (road.names.get(primary) or ''):
        return ""
    road_text = ' / '.join([gen_single_road_code(code, region) for code in road.code]) \
        + (" " if road.code else "") \
        + (road.names.get(primary) or '')
    for lang in secondary:
        name = road.names.get(lang) or ''
        if name:
            road_text += '\n  ' + name
    return road_text

def split_road_block(block: str) -> tuple[str, str]:
    """把道路块拆分为 (主行, 副语言行)。单行块（无副语言）副语言部分为空字符串"""
    parts = block.split('\n', 1)
    main_line = parts[0]
    tail = parts[1] if len(parts) > 1 else ''
    return main_line, tail


def merge_itrchg_and_toll_station(in_list):
    """处理立交和收费站的合并事宜。列表中如果有“互通”“立交”“枢纽”“入口”“出口”和“收费站”结尾的项目相连，则合并为 “XX互通/立交/枢纽（XXX收费站）

    多语言多行块以副语言行（英文等）结尾，endswith 检测若作用于整块将永不命中；
    故后缀判断只看每块的主行（首行）。合并后的主行以“主导名称”块（情况1 的当前块、
    情况2 的下一块，即不带括号的那一方）为准，并保留该块的副语言行；被并入括号的
    （收费站）块不带编号/无独立主名，其副语言行不保留。
    """
    hint_words = ["互通", "立交", "枢纽", "入口", "出口"]  # 指示词后缀
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
        current_main, current_tail = split_road_block(current)
        next_main, next_tail = split_road_block(next_item)

        # 情况1：当前是指示词，下一个是收费站（主名与副语言行均取当前互通块）
        if any(current_main.endswith(word) for word in hint_words) and next_main.endswith(toll_suffix):
            merged = f"{current_main}（{next_main}）"
            if current_tail:
                merged += '\n' + current_tail
            should_merge = True

        # 情况2：当前是收费站，下一个是指示词（主名与副语言行均取下一互通块）
        elif current_main.endswith(toll_suffix) and any(next_main.endswith(word) for word in hint_words):
            merged = f"{next_main}（{current_main}）"
            if next_tail:
                merged += '\n' + next_tail
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

def gen_route_info(city_info_list: list[CityInfo], region: Region = Region.CN) -> str:
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

    兼容性前提：CN 地区输出与旧版字节级一致，仅当 CSV 的 *_en 字段全部为空。若 *_en 非空，
    将按语言集（副语言 en）额外输出「英语：」区/市对照行与缩进路名行——这是有意的能力扩展；
    ID 地区同理输出印尼语/英语对照行。
    """
    primary, secondary = get_default_languages(region)
    city_timeline_text = ''
    city_road_list = []
    for city_i, city in enumerate(city_info_list):
        area_timeline_text = ''
        area_road_list = []
        # 城市级副语言对照行：省名 · 城市名（逐行带语言前缀）
        city_secondary_lines = []
        for lang in secondary:
            pair = city.names.get(lang)
            if not pair:
                continue
            parts = [value for value in pair if value]
            if parts:
                city_secondary_lines.append(LANG_PREFIX[lang] + ' · '.join(parts))
        city_secondary_text = ''.join(line + '\n' for line in city_secondary_lines)
        for area_i, area in enumerate(city.areas):
            road_text_list = [gen_single_road_info(road, region) for road in area.roads]
            road_text_list = merge_itrchg_and_toll_station(road_text_list)
            road_text_list = merge_empty_items(road_text_list)
            # 如果 road_text_list 第一项与它的前一个路相同，则给两边加上省略号。
            # 前一个路指前一个区（或上一个市的末区）的最后一条路；该区的路可能全部为空
            # （空行被 merge_empty_items 剔除）从而合并成空列表，读取前路前须逐级防空列表
            if road_text_list and (city_i != 0 or area_i != 0):
                if area_i == 0:
                    # 前一个路在上一个市里面（该市的最后一个区）
                    prev_roads = city_road_list[-1][-1] if city_road_list and city_road_list[-1] else []
                else:
                    # 前一个路在上一个区里面，注意此时该区还未写入 city_road_list
                    prev_roads = area_road_list[-1] if area_road_list and area_road_list[-1] else []
                if prev_roads and road_text_list[0].replace('…', '') == prev_roads[-1].replace('…', ''):
                    road_text_list[0] = '…' + road_text_list[0]
                    # prev_roads 是已（或将）存入 city_road_list 的同一列表对象，原地修改生效
                    prev_roads[-1] = prev_roads[-1] + '…'
            area_road_list.append(road_text_list)
            # 区级副语言对照行：仅区名（逐行带语言前缀）
            area_secondary_lines = []
            for lang in secondary:
                area_name = area.names.get(lang) or ''
                if area_name:
                    area_secondary_lines.append(LANG_PREFIX[lang] + area_name)
            area_secondary_text = ''.join(line + '\n' for line in area_secondary_lines)
            area_timeline_text += '\n' + AREA_TIMELINE_TEMPLATE \
                .replace('{{area}}', area.names.get(primary, '')) \
                .replace('{{area_secondary}}', area_secondary_text)
        city_road_list.append(area_road_list)
        city_timeline_text += '\n' + CITY_TIMELINE_TEMPLATE \
            .replace('{{province}}', city.province) \
            .replace('{{city}}', city.city) \
            .replace('{{city_secondary}}', city_secondary_text) \
            .replace('{{areas_info}}', area_timeline_text)
    for city_roads in city_road_list:
        for area_roads in city_roads:
            # 道路均为单行（无副语言路名）时沿用 → 连接；含副语言行则逐块换行
            sep = ' → ' if all('\n' not in item for item in area_roads) else '\n'
            city_timeline_text = city_timeline_text.replace('{{road_info}}', sep.join(area_roads), 1)
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