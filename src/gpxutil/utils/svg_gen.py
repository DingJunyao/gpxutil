from functools import reduce
import xml.etree.ElementTree as ET

import svgwrite
from svgwrite import Drawing
from svgpathtools import svg2paths
from svgpathtools import parse_path
from svgpathtools.path import Path

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

from src.gpxutil.core.config import CONFIG_HANDLER
from src.gpxutil.models.indonesia import IndonesiaRoadLevel

# Brown  -- Panose 469 -- RGB 97,54,29  61361D
# Green  -- Panose 342 -- RGB 0,110,85  006E55
# Red    -- Panose 187 -- RGB 181,39,60 B5273C
# Blue   -- Panose 294 -- RGB 0,62,134  003E86
# Yellow -- Panose 116 -- RGB 255,205,0 FFCD00
# Orange -- Panose 152 -- RGB 230,113,0 E67100

# Brown  -- CMYK 38/63/93/36 -- RGB 119,78,36   774E24
# Green  -- CMYK 100/0/79/9  -- RGB 0,155,103   007367
# Red    -- CMYK 0/100/65/0  -- RGB 237,23,36   ED1724
# Blue   -- CMYK 93/57/2/0   -- RGB 0,107,177   006BB1
# Yellow -- CMYK 0/0/100/0   -- RGB 255,242,0   FFF200
# Orange -- CMYK 0/51/87/0   -- RGB 247,146,51  F79233

# 此部分应该从配置文件中读取
RED = ''
WHITE = ''
YELLOW = ''
BLACK = ''
GREEN = ''
EXPWY_TEMPLATE_DICT = {
    '1': '',
    '2': '',
    '4': '',
    '1_name': '',
    '2_name': '',
    '4_name': '',
}

# 此部分按照模板和国标硬编码
WAY_NUM_PAD_WIDTH = 400
WAY_NUM_PAD_HEIGHT = 200
WAY_NUM_PAD_WORD_START_X = 50
WAY_NUM_PAD_WORD_START_Y = 50
WAY_NUM_PAD_WORD_WIDTH = 300
WAY_NUM_PAD_WORD_HEIGHT = 100


EXPWY_CODE_START_X_DICT = {
    '1': 150,
    '2': 90,
    '4_big': 90,
    '4_small': 1220,
}
EXPWY_CODE_START_Y_DICT = {
    'big': 370,
    'big_name': 340,
    'small': 520,
    'small_name': 490,
}
EXPWY_CODE_WIDTH_DICT = {
    '1': 700,
    '2_4_big': 1070,
    '4_small': 390,
}
EXPWY_CODE_HEIGHT_DICT = {
    'big': 450,
    'small': 300,
}
EXPWY_NAME_START_X_DICT = {
    '1': 100,
    '2_4': 150,
}
EXPWY_NAME_START_Y = 860
EXPWY_NAME_WIDTH_DICT = {
    1: 800,
    2: 950,
    4: 1400,
}
EXPWY_NAME_HEIGHT = 200

EXPWY_BANNER_TEXT_START_X_DICT = {
    'national_1': 150,
    'national_2': 275,
    '4': 355,
    'province_1': 250,
    'province_2': 359.1,
}
EXPWY_BANNER_TEXT_START_Y_DICT = {
    'without_name': 80,
    'with_name': 110,
}

EXPWY_BANNER_TEXT_WIDTH_DICT = {
    'national_1_2': 700,
    '4': 990,
    'province_1_2': 500
}
EXPWY_BANNER_TEXT_HEIGHT = 100


def set_const():
    """
    读配置，写入对应的变量，供使用。应该在使用它们的函数最开始执行。
    :return: None
    """
    global RED, WHITE, YELLOW, BLACK, GREEN, EXPWY_TEMPLATE_DICT
    RED = CONFIG_HANDLER.config.traffic_sign.color.red
    WHITE = CONFIG_HANDLER.config.traffic_sign.color.white
    YELLOW = CONFIG_HANDLER.config.traffic_sign.color.yellow
    BLACK = CONFIG_HANDLER.config.traffic_sign.color.black
    GREEN = CONFIG_HANDLER.config.traffic_sign.color.green
    EXPWY_TEMPLATE_DICT = {
        '1': CONFIG_HANDLER.config.traffic_sign.expwy_code_sign.without_name.num_1.template_path,
        '2': CONFIG_HANDLER.config.traffic_sign.expwy_code_sign.without_name.num_2.template_path,
        '4': CONFIG_HANDLER.config.traffic_sign.expwy_code_sign.without_name.num_4.template_path,
        '1_name': CONFIG_HANDLER.config.traffic_sign.expwy_code_sign.with_name.num_1.template_path,
        '2_name': CONFIG_HANDLER.config.traffic_sign.expwy_code_sign.with_name.num_2.template_path,
        '4_name': CONFIG_HANDLER.config.traffic_sign.expwy_code_sign.with_name.num_4.template_path,
    }

def char_to_svg_path(font_path, char) -> Path:
    # 加载字体
    font = TTFont(font_path)

    # 获取字符对应的字形名称
    cmap = font.getBestCmap()
    glyph_name = cmap[ord(char)]

    # 获取字形对象
    glyph_set = font.getGlyphSet()
    glyph = glyph_set[glyph_name]

    # 创建SVG路径
    pen = SVGPathPen(glyph_set)
    glyph.draw(pen)
    svg_path = pen.getCommands()
    # 输出图形会上下颠倒
    return parse_path(svg_path).scaled(1, -1)


def get_svg_dimensions(svg_path: str):
    """
    获取 SVG 文件的尺寸。
    :param svg_path: 路径
    :return: 宽、高
    """
    # 解析 SVG 文件
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 获取 <svg> 标签的 width 和 height 属性
    width = root.get('width')
    height = root.get('height')

    if not width or not height:
        view_box = [float(i) for i in root.get('viewBox').split(' ')]
        width_value = view_box[2] - view_box[0]
        height_value = view_box[3] - view_box[1]
    else:
        # 解析这些值，它们可能是带有单位的字符串（如 "100px", "100%"）
        # 这里假设单位是像素（"px"），如果不是，则需要额外处理
        width_value = float(width.strip('px')) if 'px' in width else float(width)
        height_value = float(height.strip('px')) if 'px' in height else float(height)
    return width_value, height_value


def calculate_scaled_char_info(code: str, start_x: int | float, start_y: int | float, width: int | float, height: int | float, font: str):
    """
    给定一段单行文字，这段文字的起始坐标，文本块的宽高，以及使用的字体，给出各个文字的 SVG Path。排版时假定所有字符都等高。
    :param code: 文字
    :param start_x: 文本块起始 x
    :param start_y: 文本块起始 y
    :param width: 文本块宽
    :param height: 文本块高
    :param font: 字体所在目录
    :return: 各个文字的 SVG Path 组成的列表
    """
    scaled_char_path_list = []
    scaled_char_width_list = []
    char_pos_list = []
    for i in code:
        # i_ord = 'u{:0>4x}'.format(ord(i))
        # input_file_char = '{}/u{:0>4x}.svg'.format(font, ord(i))
        # paths_char, attributes_char = svg2paths(input_file_char)
        # char_minx, char_maxx, char_miny, char_maxy = paths_char[0].bbox()
        paths_char = char_to_svg_path(font, i)
        char_minx, char_maxx, char_miny, char_maxy = paths_char.bbox()
        char_width = char_maxx - char_minx
        char_height = char_maxy - char_miny
        ratio = height / char_height
        # print('original %s: (%s, %s), (%s * %s)' % (i, char_minx, char_miny, char_width, char_height))
        # scaled_path_char = paths_char[0].scaled(ratio)
        scaled_path_char = paths_char.scaled(ratio)
        scaled_char_minx, scaled_char_maxx, scaled_char_miny, scaled_char_maxy = scaled_path_char.bbox()
        scaled_char_width = scaled_char_maxx - scaled_char_minx
        scaled_char_height = scaled_char_maxy - scaled_char_miny
        scaled_path_char = scaled_path_char.translated(complex(-scaled_char_minx, -scaled_char_miny))
        # print('scaled %s: (%s, %s), (%s * %s)' % (i, scaled_char_minx, scaled_char_miny, scaled_char_width, scaled_char_height))
        scaled_char_width_list.append(scaled_char_width)
        scaled_char_path_list.append(scaled_path_char)
    if len(code) > 1:
        space = (width - reduce(lambda x, y: x + y, scaled_char_width_list)) / (len(code) - 1)
    else:
        space = 0
    # print('space: %s' % space)
    char_x = start_x
    char_y = start_y
    for i, char_width in enumerate(scaled_char_width_list):
        if i != 0:
            char_x += scaled_char_width_list[i - 1] + space
        char_pos_list.append((char_x, char_y))
    scaled_char_path_list = [path.translated(complex(*pos)) for path, pos in zip(scaled_char_path_list, char_pos_list)]
    return scaled_char_path_list

def generate_way_num_pad(code: str):
    set_const()
    match code[0]:
        case 'G':
            background_color = RED
            stroke_color = WHITE
        case 'S':
            background_color = YELLOW
            stroke_color = BLACK
        case _:
            background_color = WHITE
            stroke_color = BLACK


    paths, attributes = svg2paths(CONFIG_HANDLER.config.traffic_sign.way_num_pad.template_path)

    scaled_char_path_list = calculate_scaled_char_info(
        code, WAY_NUM_PAD_WORD_START_X, WAY_NUM_PAD_WORD_START_Y, WAY_NUM_PAD_WORD_WIDTH, WAY_NUM_PAD_WORD_HEIGHT,
        CONFIG_HANDLER.config.traffic_sign.font_path.B
    )

    dwg = svgwrite.Drawing('output.svg', size=(f'{WAY_NUM_PAD_WIDTH}', f'{WAY_NUM_PAD_HEIGHT}'))
    for path, attr in zip(paths, attributes):
        insert_x = 0
        insert_y = 0
        insert_rx = 0
        insert_ry = 0
        fill = stroke_color
        if 'x' in attr:
            insert_x = attr['x']
        if 'y' in attr:
            insert_y = attr['y']
        if 'rx' in attr:
            insert_rx = attr['rx']
        if 'ry' in attr:
            insert_ry = attr['ry']
        if 'class' in attr:
            if attr['class'] == 'background':
                fill = background_color
            if attr['class'] == 'stroke':
                fill = stroke_color
        dwg.add(dwg.rect(insert=(insert_x, insert_y), size=(attr['width'], attr['height']), rx=insert_rx, ry=insert_ry, fill=fill))
    for path in scaled_char_path_list:
        dwg.add(dwg.path(d=path.d(), fill=stroke_color))
    return dwg


def generate_way_num_pad_to_file(code: str, path: str):
    generate_way_num_pad(code).saveas(path)

def generate_expwy_pad(code: str, province: str = None, name: str = None):
    set_const()
    code_start_x_index: str = '2'
    code_start_y_index: str = 'big'
    code_width_index: str = '2_4_big'
    code_height_index: str = 'big'

    small_code_start_x_index: str = '4_small'
    small_code_start_y_index: str = 'small'
    small_code_width_index: str = '4_small'
    small_code_height_index: str = 'small'

    name_start_x_index: str = '2_4'
    # EXPWY_NAME_START_Y
    name_width_index: int = 2
    # EXPWY_NAME_HEIGHT

    banner_text_start_x_index: str = ''
    banner_text_start_y_index: str = 'without_name'
    banner_text_width_index: str = ''
    # EXPWY_BANNER_TEXT_HEIGHT

    banner_text = '国家高速'

    background_color = GREEN
    banner_color = RED
    banner_char_color = WHITE
    stroke_color = WHITE

    if province:
        banner_text = province + '高速'
        if not code.startswith('S'):
            code = 'S' + code
        banner_color = YELLOW
        banner_char_color = BLACK
        banner_text_start_x_index = 'province_'
    else:
        banner_text_start_x_index = 'national_'
        if not code.startswith('G'):
            code = 'G' + code

    code_num_len = len(code) - 1
    banner_text_start_x_index += str(code_num_len)

    if code_num_len == 4:
        banner_text_width_index = '4'
        banner_text_start_x_index = '4'
    elif province:
        banner_text_width_index = 'province_1_2'
    else:
        banner_text_width_index = 'national_1_2'

    template_index = str(len(code) - 1)
    if name:
        template_index += '_name'
        code_start_y_index = 'big_name'
        small_code_start_y_index = 'small_name'
        banner_text_start_y_index = 'with_name'

    match code_num_len:
        case 1:
            code_start_x_index = '1'
            code_width_index = '1'
            name_start_x_index = '1'
            name_width_index = 1
        case 2:
            code_start_x_index = '2'
            code_width_index = '2_4_big'
            name_start_x_index = '2_4'
            name_width_index = 2
        case 4:
            code_start_x_index = '4_big'
            code_width_index = '2_4_big'
            name_start_x_index = '2_4'
            name_width_index = 4

    big_code = None
    small_code = None
    if code_num_len == 4:
        big_code = code[:3]
        small_code = code[3:]
    else:
        big_code = code

    paths, attributes = svg2paths(EXPWY_TEMPLATE_DICT[template_index])

    scaled_banner_text_char_path_list = calculate_scaled_char_info(
        banner_text, EXPWY_BANNER_TEXT_START_X_DICT[banner_text_start_x_index],
        EXPWY_BANNER_TEXT_START_Y_DICT[banner_text_start_y_index],
        EXPWY_BANNER_TEXT_WIDTH_DICT[banner_text_width_index], EXPWY_BANNER_TEXT_HEIGHT,
        CONFIG_HANDLER.config.traffic_sign.font_path.A
    )

    scaled_big_code_char_path_list = calculate_scaled_char_info(
        big_code, EXPWY_CODE_START_X_DICT[code_start_x_index], EXPWY_CODE_START_Y_DICT[code_start_y_index],
        EXPWY_CODE_WIDTH_DICT[code_width_index], EXPWY_CODE_HEIGHT_DICT[code_height_index],
        CONFIG_HANDLER.config.traffic_sign.font_path.B
    )
    if small_code:
        scaled_small_code_char_path_list = calculate_scaled_char_info(
            small_code, EXPWY_CODE_START_X_DICT[small_code_start_x_index],
            EXPWY_CODE_START_Y_DICT[small_code_start_y_index], EXPWY_CODE_WIDTH_DICT[small_code_width_index],
            EXPWY_CODE_HEIGHT_DICT[small_code_height_index], CONFIG_HANDLER.config.traffic_sign.font_path.C
        )
    if name:
        scaled_name_char_path_list = calculate_scaled_char_info(
            name, EXPWY_NAME_START_X_DICT[name_start_x_index], EXPWY_NAME_START_Y, EXPWY_NAME_WIDTH_DICT[name_width_index],
            EXPWY_NAME_HEIGHT, CONFIG_HANDLER.config.traffic_sign.font_path.A
        )

    dwg = svgwrite.Drawing('output.svg', size=tuple([str(i) for i in get_svg_dimensions(EXPWY_TEMPLATE_DICT[template_index])]))
    for path, attr in zip(paths, attributes):
        fill = WHITE
        if 'class' in attr:
            if attr['class'] == 'background':
                fill = background_color
            if attr['class'] == 'stroke':
                fill = stroke_color
            if attr['class'] == 'banner':
                fill = banner_color
            # if attr['class'] == 'banner_text':
            #     fill = banner_char_color
        dwg.add(dwg.path(d=path.d(), fill=fill))
    for path in scaled_banner_text_char_path_list:
        dwg.add(dwg.path(d=path.d(), fill=banner_char_color))
    for path in scaled_big_code_char_path_list:
        dwg.add(dwg.path(d=path.d(), fill=stroke_color))
    if small_code:
        for path in scaled_small_code_char_path_list:
            dwg.add(dwg.path(d=path.d(), fill=stroke_color))
    if name:
        for path in scaled_name_char_path_list:
            dwg.add(dwg.path(d=path.d(), fill=stroke_color))
    return dwg


def generate_expwy_pad_to_file(path: str, code: str, province: str = None, name: str = None):
    generate_expwy_pad(code, province, name).saveas(path)


INDONESIA_LEVEL_BANNER_TEXT = {
    IndonesiaRoadLevel.NASIONAL: 'NASIONAL',
    IndonesiaRoadLevel.TOL: 'TOL',
    IndonesiaRoadLevel.PROVINSI: 'PROVINSI',
}


def _parse_polygon_points(points: str) -> list[tuple[float, float]]:
    """解析 polygon 的 points 属性为坐标对列表（兼容逗号与空格分隔）。"""
    nums = [float(v) for v in points.replace(',', ' ').split()]
    return list(zip(nums[0::2], nums[1::2]))


def get_element_bbox_by_id(svg_path: str, element_id: str):
    """
    解析 SVG 模板，取指定 id 元素的 bbox（支持 polygon）。
    :return: (xmin, ymin, xmax, ymax)；找不到该 id 的元素返回 None
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()
    for elem in root.iter():
        if elem.attrib.get('id') == element_id:
            if elem.tag.split('}')[-1] == 'polygon':
                points = _parse_polygon_points(elem.attrib.get('points', ''))
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                return min(xs), min(ys), max(xs), max(ys)
            return None
    return None


def _get_back_group_elements(svg_path: str) -> list[tuple[str, dict]]:
    """
    解析印尼盾牌模板文件，取 id='back' 组内的绘制元素（跳过 id='text' 占位字形组）。
    模板多边形不被 svg2paths 解析，这里用 XML 直接取出。

    :return: 按文档顺序的 (标签名, 属性字典) 列表；head 多边形以 id='head' 属性标识，便于上色
    :raise ValueError: 模板中找不到 id='back' 的组
    """
    root = ET.parse(svg_path).getroot()
    back_group = None
    for elem in root.iter():
        if elem.tag.split('}')[-1] == 'g' and elem.attrib.get('id') == 'back':
            back_group = elem
            break
    if back_group is None:
        raise ValueError(f'印尼盾牌模板 {svg_path} 中找不到 id=back 的元素')
    result = []
    for elem in back_group:
        tag = elem.tag.split('}')[-1]
        if tag == 'g' and elem.attrib.get('id') == 'background':
            # 展开背景组：白色六边形 polygon + 黑色描边 path，保持模板内顺序
            for child in elem:
                result.append((child.tag.split('}')[-1], child.attrib))
        else:
            result.append((tag, elem.attrib))
    return result


def calculate_centered_scaled_char_info(code: str, center_x: float, center_y: float,
                                        height: float, font: str) -> list[Path]:
    """
    按固定高度缩放一段文字，水平居中于 center_x、垂直居中于 center_y（无额外字距）。
    空格无字形轮廓：按字体 ascent 比例换算其 advance 宽度占位排版，生成占位 path 保持
    与字符一一对应（不绘制像素），保证与字形 path 同样的绘制流程。

    :param code: 文字
    :param center_x: 文字水平中心 x
    :param center_y: 文字垂直中心 y
    :param height: 文字高度
    :param font: 字体文件路径
    :return: 各字符（含空格）path 列表
    :raise ValueError: 文字为空
    """
    if not code:
        raise ValueError('文字为空，无法生成字形 path')
    font_obj = None
    space_scale = 0.0
    space_advance = 0.0
    scaled_char_path_list = []
    scaled_char_width_list = []
    for char in code:
        if char == ' ':
            if font_obj is None:
                font_obj = TTFont(font)
                # 字形按各自轮廓 bbox 高度缩放到 height，其纵向跨度约为基线到字帽高度
                # （Clearview 约 1000-1033 / 1448 em）；ascent 与该跨度同一量级，
                # 空格无轮廓，故以 ascent 作统一纵向基准把 advance（字面宽）换算到像素，
                # 使空格视觉宽度与相邻字形宽度比例协调。此为近似值，勿按 bug 修改。
                space_scale = height / font_obj['hhea'].ascent
                space_glyph = font_obj.getBestCmap()[ord(' ')]
                space_advance = font_obj['hmtx'][space_glyph][0]
            scaled_char_width_list.append(space_advance * space_scale)
            scaled_char_path_list.append(None)
            continue
        paths_char = char_to_svg_path(font, char)
        char_minx, char_maxx, char_miny, char_maxy = paths_char.bbox()
        char_height = char_maxy - char_miny
        ratio = height / char_height
        scaled_path_char = paths_char.scaled(ratio)
        scaled_char_minx, scaled_char_maxx, scaled_char_miny, scaled_char_maxy = scaled_path_char.bbox()
        scaled_char_width = scaled_char_maxx - scaled_char_minx
        scaled_path_char = scaled_path_char.translated(complex(-scaled_char_minx, -scaled_char_miny))
        scaled_char_width_list.append(scaled_char_width)
        scaled_char_path_list.append(scaled_path_char)

    total_width = reduce(lambda x, y: x + y, scaled_char_width_list)
    start_x = center_x - total_width / 2
    start_y = center_y - height / 2
    char_x = start_x
    result = []
    for path, width in zip(scaled_char_path_list, scaled_char_width_list):
        if path is None:
            # 空格占位：零长度退化 path（M 0,0h0），只占排版位置、不绘制像素
            path = parse_path('M 0,0h0')
        result.append(path.translated(complex(char_x, start_y)))
        char_x += width
    return result


def generate_indonesia_shield(code: str, road_level: IndonesiaRoadLevel,
                              province_code: str | None) -> Drawing:
    """
    生成印尼六边形道路盾牌。布局由模板元素 bbox 推导。
    模板 id='text' 组为占位字形（display:none），不绘制，仅画背景与色带。

    :param code: 道路编号（盾牌大字），如 '3'、'024'；为空或 None 视为参数错误
    :param road_level: 道路等级，决定色带颜色与等级词
    :param province_code: 省份代码（色带小字部分），可为 None
    :return: svgwrite Drawing
    :raise ValueError: code 为空或 road_level 不在 IndonesiaRoadLevel 中
    """
    if not code:
        raise ValueError('code 为空，无法生成盾牌')
    if road_level not in INDONESIA_LEVEL_BANNER_TEXT:
        raise ValueError(f'未知的印尼道路等级: {road_level}')
    set_const()
    cfg = CONFIG_HANDLER.config.traffic_sign.indonesia_road_sign
    blue = CONFIG_HANDLER.config.traffic_sign.color.blue

    # 色带颜色：国道/高速红色，省道蓝色
    head_fill = RED
    if road_level == IndonesiaRoadLevel.PROVINSI:
        head_fill = blue

    banner_text = INDONESIA_LEVEL_BANNER_TEXT[road_level]
    if province_code:
        banner_text += f' {province_code}'

    width, height = get_svg_dimensions(cfg.template_path)
    head_bbox = get_element_bbox_by_id(cfg.template_path, 'head')
    if head_bbox is None:
        raise ValueError(f'印尼盾牌模板 {cfg.template_path} 中找不到 id=head 的元素')
    center_x = width / 2
    head_center_y = (head_bbox[1] + head_bbox[3]) / 2
    lower_center_y = (head_bbox[3] + height) / 2

    dwg = svgwrite.Drawing('output.svg', size=(f'{width:g}', f'{height:g}'))
    # 模板背景：白色六边形 → 黑色描边 → 色带（保持顺序，使色带覆盖描边顶部）
    for tag, attrib in _get_back_group_elements(cfg.template_path):
        if tag == 'polygon':
            if attrib.get('id') == 'head':
                fill = head_fill
                polygon = dwg.polygon(points=_parse_polygon_points(attrib['points']), fill=fill, id='head')
            else:
                fill = WHITE
                polygon = dwg.polygon(points=_parse_polygon_points(attrib['points']), fill=fill)
            dwg.add(polygon)
        elif tag == 'path':
            # svgwrite 不接受模板里紧凑的 path 语法，先解析再序列化
            dwg.add(dwg.path(d=parse_path(attrib['d']).d(), fill=BLACK))

    # 色带小字（白）与大字（黑）
    for path in calculate_centered_scaled_char_info(
            banner_text, center_x, head_center_y, cfg.font.upper_height, cfg.font.upper):
        dwg.add(dwg.path(d=path.d(), fill=WHITE))
    for path in calculate_centered_scaled_char_info(
            code, center_x, lower_center_y, cfg.font.lower_height, cfg.font.lower):
        dwg.add(dwg.path(d=path.d(), fill=BLACK))
    return dwg


def generate_indonesia_shield_to_file(code: str, road_level: IndonesiaRoadLevel,
                                      province_code: str | None, path: str):
    generate_indonesia_shield(code, road_level, province_code).saveas(path)


if __name__ == '__main__':
    generate_way_num_pad_to_file('G221', './out/G221.svg')
    generate_way_num_pad_to_file('S221', './out/S221.svg')
    generate_way_num_pad_to_file('X221', './out/X221.svg')
    generate_expwy_pad_to_file('./out/expwy_01.svg', 'G5')
    generate_expwy_pad_to_file('./out/expwy_02.svg', 'G45')
    generate_expwy_pad_to_file('./out/expwy_03.svg', 'G4511')
    generate_expwy_pad_to_file('./out/expwy_07.svg', 'S2', '豫')
    generate_expwy_pad_to_file('./out/expwy_08.svg', 'S21', '豫')
    generate_expwy_pad_to_file('./out/expwy_09.svg', 'S0211', '豫')
    generate_expwy_pad_to_file('./out/expwy_04.svg', 'G5', name='测测高速')
    generate_expwy_pad_to_file('./out/expwy_05.svg', 'G45', name='测试高速')
    generate_expwy_pad_to_file('./out/expwy_06.svg', 'G4511', name='测试测试高速')
    generate_expwy_pad_to_file('./out/expwy_10.svg', 'S2', '豫', name='测试省级')
    generate_expwy_pad_to_file('./out/expwy_11.svg', 'S21', '豫', name='测试省高')
    generate_expwy_pad_to_file('./out/expwy_12.svg', 'S0211', '豫', name='测试省级高速')
    generate_way_num_pad_to_file('G318', './out/G318.svg')
    generate_expwy_pad_to_file('./out/expwy_G2503.svg', 'G2503', name='南京绕城高速')
    generate_expwy_pad_to_file('./out/expwy_shanxi_S75.svg', 'S75', '晋')
    generate_way_num_pad_to_file('G318', './out/G318-red.svg')