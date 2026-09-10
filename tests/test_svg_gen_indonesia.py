import xml.etree.ElementTree as ET

from src.gpxutil.models.indonesia import IndonesiaRoadLevel
from src.gpxutil.utils.svg_gen import generate_indonesia_shield


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
