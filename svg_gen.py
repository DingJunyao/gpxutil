from functools import reduce
import xml.etree.ElementTree as ET
from tempfile import template

import svgwrite
from svgpathtools import svg2paths
from svgpathtools import parse_path
from svgpathtools.path import Path

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

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

RED = '#B5273C'
WHITE = '#FFFFFF'
YELLOW = '#FFCD00'
BLACK = '#000000'
GREEN = '#006E55'
WAY_NUM_PAD_WIDTH = 400
WAY_NUM_PAD_HEIGHT = 200
WAY_NUM_PAD_WORD_START_X = 50
WAY_NUM_PAD_WORD_START_Y = 50
WAY_NUM_PAD_WORD_WIDTH = 300
WAY_NUM_PAD_WORD_HEIGHT = 100

WAY_NUM_PAD_TEMPLATE = 'asset/template/way_num.svg'
# FONT_TYPE_DIRECTORY_DICT = {
#     'A': 'asset/source_han_sans_cn_bold',
#     'B': 'asset/jtbz_b',
#     'C': 'asset/jtbz_c'
# }
FONT_TYPE_DIRECTORY_DICT = {
    'A': 'asset/SourceHanSansSC-Bold.otf',
    'B': 'asset/jtbz_B.ttf',
    'C': 'asset/jtbz_C.ttf'
}
EXPWY_TEMPLATE_DICT = {
    '1': 'asset/template/expwy_1.svg',
    '2': 'asset/template/expwy_2.svg',
    '4': 'asset/template/expwy_4.svg',
    '1_name': 'asset/template/expwy_1_name.svg',
    '2_name': 'asset/template/expwy_2_name.svg',
    '4_name': 'asset/template/expwy_4_name.svg',
}
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

# EXPWY_BANNER_TEXT_START_X_DICT = {
#     1: 250,
#     2: 359.1,
#     4: 600
# }
# EXPWY_BANNER_TEXT_START_Y_DICT = {
#     'without_name': 80,
#     'with_name': 110,
# }
# EXPWY_BANNER_TEXT_WIDTH = 100
# EXPWY_BANNER_TEXT_HEIGHT = 100

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
# EXPWY_BANNER_TEXT_WIDTH = 95.7212
EXPWY_BANNER_TEXT_WIDTH_DICT = {
    'national_1_2': 700,
    '4': 990,
    'province_1_2': 500
}
EXPWY_BANNER_TEXT_HEIGHT = 100


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


    paths, attributes = svg2paths(WAY_NUM_PAD_TEMPLATE)

    scaled_char_path_list = calculate_scaled_char_info(code, WAY_NUM_PAD_WORD_START_X, WAY_NUM_PAD_WORD_START_Y, WAY_NUM_PAD_WORD_WIDTH, WAY_NUM_PAD_WORD_HEIGHT, FONT_TYPE_DIRECTORY_DICT['B'])

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
        FONT_TYPE_DIRECTORY_DICT['A']
    )

    scaled_big_code_char_path_list = calculate_scaled_char_info(
        big_code, EXPWY_CODE_START_X_DICT[code_start_x_index], EXPWY_CODE_START_Y_DICT[code_start_y_index],
        EXPWY_CODE_WIDTH_DICT[code_width_index], EXPWY_CODE_HEIGHT_DICT[code_height_index],
        FONT_TYPE_DIRECTORY_DICT['B']
    )
    if small_code:
        scaled_small_code_char_path_list = calculate_scaled_char_info(
            small_code, EXPWY_CODE_START_X_DICT[small_code_start_x_index],
            EXPWY_CODE_START_Y_DICT[small_code_start_y_index], EXPWY_CODE_WIDTH_DICT[small_code_width_index],
            EXPWY_CODE_HEIGHT_DICT[small_code_height_index], FONT_TYPE_DIRECTORY_DICT['C']
        )
    if name:
        scaled_name_char_path_list = calculate_scaled_char_info(
            name, EXPWY_NAME_START_X_DICT[name_start_x_index], EXPWY_NAME_START_Y, EXPWY_NAME_WIDTH_DICT[name_width_index],
            EXPWY_NAME_HEIGHT, FONT_TYPE_DIRECTORY_DICT['A']
        )

    dwg = svgwrite.Drawing('output.svg', size=tuple([str(i) for i in get_svg_dimensions(EXPWY_TEMPLATE_DICT[template_index])]))
    for path, attr in zip(paths, attributes):
        fill = '#ffffff'
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