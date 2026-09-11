import xml.etree.ElementTree as ET

from src.gpxutil.models.indonesia import IndonesiaRoadLevel
from src.gpxutil.utils.svg_gen import calculate_centered_scaled_char_info, generate_indonesia_shield


def test_nasional_shield():
    dwg = generate_indonesia_shield('3', IndonesiaRoadLevel.NASIONAL, '16')
    svg = ET.fromstring(dwg.tostring())
    # head 色带为红色
    head = svg.find(".//*[@id='head']")
    assert head is not None
    assert head.get('fill') == '#B5273C'


def test_provinsi_shield_blue():
    dwg = generate_indonesia_shield('024', IndonesiaRoadLevel.PROVINSI, '16')
    svg = ET.fromstring(dwg.tostring())
    head = svg.find(".//*[@id='head']")
    assert head.get('fill') == '#003E86'


def test_text_paths_present():
    dwg = generate_indonesia_shield('3', IndonesiaRoadLevel.NASIONAL, '16')
    svg = ET.fromstring(dwg.tostring())
    paths = svg.findall('.//{http://www.w3.org/2000/svg}path')
    # 背景 path + 色带小字（'NASIONAL 16'，11 字符，含空格占位）+ 大字（'3'，1 字符）
    assert len(paths) == 1 + len('NASIONAL 16') + len('3')


def test_no_region_code_banner_text():
    # 无地区代码时色带只有等级词（'TOL' 3 字符）
    dwg = generate_indonesia_shield('8', IndonesiaRoadLevel.TOL, None)
    svg = ET.fromstring(dwg.tostring())
    paths = svg.findall('.//{http://www.w3.org/2000/svg}path')
    assert len(paths) == 1 + len('TOL') + len('8')


def test_char_spacing_from_advance():
    # 步进按 hmtx advance width 缩放，相邻字符轮廓间应保留字体默认左右留白
    paths = calculate_centered_scaled_char_info('35', 100.0, 100.0, 50.0,
                                                'asset/font/ClearviewHwy2W.ttf')
    _, first_maxx, _, _ = paths[0].bbox()
    second_minx, _, _, _ = paths[1].bbox()
    assert first_maxx < second_minx


def test_chars_centered_on_given_point():
    # 全部字符（含空格占位）合成的 bbox 应水平居中于 center_x、垂直居中于 center_y
    code = '3 5'
    center_x, center_y, height = 200.0, 100.0, 50.0
    paths = calculate_centered_scaled_char_info(code, center_x, center_y, height,
                                                'asset/font/ClearviewHwy2W.ttf')
    assert len(paths) == len(code)
    # bbox() 返回 (xmin, xmax, ymin, ymax)
    minx = min(p.bbox()[0] for p in paths)
    maxx = max(p.bbox()[1] for p in paths)
    miny = min(p.bbox()[2] for p in paths)
    maxy = max(p.bbox()[3] for p in paths)
    assert abs((minx + maxx) / 2 - center_x) < 0.5
    assert abs((miny + maxy) / 2 - center_y) < 0.5
    assert abs((maxy - miny) - height) < 0.5
