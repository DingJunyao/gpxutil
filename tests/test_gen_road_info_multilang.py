# 多语言 timeline（gen_road_info）测试
# 注意：与计划的测试差异——'8' 断言为 red 而非 green。
# gen_single_road_code 的 label 层看不到路名（无 road_name / tol_keywords 为空），
# 1-2 位编号一律按 NASIONAL(red) 处理（TOL 需路名关键词才能区分，plan KISS 认可此简化）。

from src.gpxutil.models.region import Region
from src.gpxutil.utils.gen_road_info import (
    gen_single_road_code, get_info, gen_route_info, merge_itrchg_and_toll_station,
)


def test_indonesia_label_colors():
    assert 'red' in gen_single_road_code('3', Region.ID)
    # 1-2 位编号默认 NASIONAL 红色：label 层无路名，无法判定 TOL
    assert 'red' in gen_single_road_code('8', Region.ID)
    assert 'blue' in gen_single_road_code('023', Region.ID)
    assert 'blue' in gen_single_road_code('16-024', Region.ID)


def test_indonesia_label_plain_code():
    # label 内为纯编号，不含地区代码
    text = gen_single_road_code('16-024', Region.ID)
    assert '024' in text
    assert '16-024' not in text


def test_cn_backcompat():
    assert gen_single_road_code('G310', Region.CN) == '{% label G310 red %}'
    assert gen_single_road_code('赣S22', Region.CN) == '赣 {% label S22 green %}'


def test_get_info_id_multilang(tmp_path):
    csv_path = tmp_path / 'id.csv'
    csv_path.write_text(
        'index,province,city,area,province_id,city_id,area_id,province_en,city_en,area_en,road_num,road_name,road_name_id,road_name_en\n'
        '0,东爪哇省,玛琅县,安佩尔加丁镇,Provinsi Jawa Timur,Kabupaten Malang,Kecamatan Ampelgading,'
        'Province of East Java,Malang Regency,Ampelgading District,023,图姆庞大街,Jl. Raya Tumpang,Tumpang Main Rd.\n',
        encoding='utf-8'
    )
    city_list = get_info(str(csv_path), Region.ID)
    assert len(city_list) == 1
    area = city_list[0].areas[0]
    assert area.names == {'zh': '安佩尔加丁镇', 'id': 'Kecamatan Ampelgading', 'en': 'Ampelgading District'}
    road = area.roads[0]
    assert road.names['id'] == 'Jl. Raya Tumpang'


def test_gen_route_info_id_multilang(tmp_path):
    csv_path = tmp_path / 'id.csv'
    csv_path.write_text(
        'index,province,city,area,province_id,city_id,area_id,province_en,city_en,area_en,road_num,road_name,road_name_id,road_name_en\n'
        '0,东爪哇省,玛琅县,安佩尔加丁镇,Provinsi Jawa Timur,Kabupaten Malang,Kecamatan Ampelgading,'
        'Province of East Java,Malang Regency,Ampelgading District,023,图姆庞大街,Jl. Raya Tumpang,Tumpang Main Rd.\n'
        '1,东爪哇省,玛琅县,安佩尔加丁镇,Provinsi Jawa Timur,Kabupaten Malang,Kecamatan Ampelgading,'
        'Province of East Java,Malang Regency,Ampelgading District,035-024,布兰塔斯街,Jl. Brantas,Brantas St.\n',
        encoding='utf-8'
    )
    city_list = get_info(str(csv_path), Region.ID)
    text = gen_route_info(city_list, Region.ID)
    assert '{% timeline 东爪哇省 玛琅县（Kabupaten Malang, Provinsi Jawa Timur // Malang Regency, Province of East Java）（视频 XX:XX） %}' in text
    assert '<!-- timeline 安佩尔加丁镇（Kecamatan Ampelgading // Ampelgading District）（视频 XX:XX） -->' in text
    assert '{% label 023 blue %} 图姆庞大街（Jl. Raya Tumpang // Tumpang Main Rd.）' in text
    assert ' → {% label 024 blue %} 布兰塔斯街（Jl. Brantas // Brantas St.）' in text
    assert '印尼语：' not in text
    assert '英语：' not in text
    assert '  Jl. Raya Tumpang' not in text
    assert '{% endtimeline %}' in text
    assert '<!-- endtimeline -->' in text


def test_get_info_cn_multilang(tmp_path):
    """CN 地区：names 含 zh/en，缺省副语言字段（无 _id 列）不报错"""
    csv_path = tmp_path / 'cn.csv'
    csv_path.write_text(
        'index,province,city,area,province_en,city_en,area_en,road_num,road_name,road_name_en\n'
        '0,河南省,三门峡市,渑池县,Henan Province,Sanmenxia City,Mianchi County,G310,黄河路,Huanghe Rd.\n',
        encoding='utf-8'
    )
    city_list = get_info(str(csv_path), Region.CN)
    assert len(city_list) == 1
    assert city_list[0].province == '河南省'
    assert city_list[0].city == '三门峡市'
    area = city_list[0].areas[0]
    assert area.names['en'] == 'Mianchi County'
    assert area.roads[0].names['en'] == 'Huanghe Rd.'
    text = gen_route_info(city_list, Region.CN)
    assert '{% timeline 河南省 三门峡市（Sanmenxia City, Henan Province）（视频 XX:XX） %}' in text
    assert '<!-- timeline 渑池县（Mianchi County）（视频 XX:XX） -->' in text
    assert '{% label G310 red %} 黄河路（Huanghe Rd.）' in text
    assert '英语：' not in text
    assert '  Huanghe Rd.' not in text


def test_cn_empty_secondary_keeps_plain_output(tmp_path):
    """CN CSV 副语言字段全空：副语言行整体跳过，输出不含 英语： 与缩进行"""
    csv_path = tmp_path / 'cn.csv'
    csv_path.write_text(
        'index,province,city,area,province_en,city_en,area_en,road_num,road_name,road_name_en\n'
        '0,北京市,北京市,东城区,,,,G310,黄河路,\n',
        encoding='utf-8'
    )
    city_list = get_info(str(csv_path), Region.CN)
    text = gen_route_info(city_list, Region.CN)
    assert '{% label G310 red %} 黄河路' in text
    assert '英语：' not in text
    assert '\n  ' not in text


def test_merge_itrchg_and_toll_station_single_line_unchanged():
    """单行块：互通+收费站合并行为与旧版一致"""
    result = merge_itrchg_and_toll_station(['新安互通', '新安收费站', '解放路'])
    assert result == ['新安互通（新安收费站）', '解放路']
    # 收费站在前、互通在后的顺序
    result = merge_itrchg_and_toll_station(['新安收费站', '新安互通'])
    assert result == ['新安互通（新安收费站）']


def test_merge_itrchg_and_toll_station_parenthesized_blocks():
    """含副语言括注的单行块：后缀判断只看主名部分，互通+收费站仍合并；
    收费站副语言括注不保留，主导块的副语言括注置于合并块末尾"""
    hint_block = '{% label G3002 green %} 新安互通（Xinan Interchange）'
    toll_block = '{% label G3002 green %} 新安收费站（Xinan Toll Station）'
    merged = '{% label G3002 green %} 新安互通（{% label G3002 green %} 新安收费站）（Xinan Interchange）'
    # 互通在前
    result = merge_itrchg_and_toll_station([hint_block, toll_block])
    assert result == [merged]
    # 收费站在前：主名以互通块为准，副语言括注亦取互通块
    result = merge_itrchg_and_toll_station([toll_block, hint_block])
    assert result == [merged]


def test_gen_route_info_prev_area_empty_roads_no_crash():
    """前一个区（或前一个市的末区）道路全空（合并后为空列表）时，
    后一个有路的区不崩溃、不加省略号"""
    rows = [
        # 北京市 东城区：路全空（无编号无路名）
        {'province': '北京市', 'city': '北京市', 'area': '东城区',
         'province_en': '', 'city_en': '', 'area_en': '',
         'road_num': '', 'road_name': '', 'road_name_en': ''},
        # 西城区：有正常路（前区为空 -> 旧的跨区省略号逻辑会 IndexError）
        {'province': '北京市', 'city': '北京市', 'area': '西城区',
         'province_en': '', 'city_en': '', 'area_en': '',
         'road_num': 'G310', 'road_name': '长安街', 'road_name_en': ''},
        # 丰台区：空路收尾（供新城市首区的跨市省略号逻辑使用）
        {'province': '北京市', 'city': '北京市', 'area': '丰台区',
         'province_en': '', 'city_en': '', 'area_en': '',
         'road_num': '', 'road_name': '', 'road_name_en': ''},
        # 天津市 和平区：新城市首个区有路（前市末区为空 -> 旧逻辑同样 IndexError）
        {'province': '天津市', 'city': '天津市', 'area': '和平区',
         'province_en': '', 'city_en': '', 'area_en': '',
         'road_num': 'G207', 'road_name': '京津高速', 'road_name_en': ''},
    ]
    city_list = get_info(rows, Region.CN)
    text = gen_route_info(city_list, Region.CN)
    assert '{% label G310 red %} 长安街' in text
    assert '{% label G207 red %} 京津高速' in text
    assert '…' not in text
