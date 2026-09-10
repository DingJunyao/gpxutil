import csv
import gc
import io
import math
import os
import string
from dataclasses import replace
from datetime import datetime
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

import cairosvg
import moviepy
from PIL import Image, ImageDraw, ImageFont
from svgwrite import Drawing
from tqdm import tqdm

import numpy as np
import imageio

from moviepy.video.io.ffmpeg_writer import ffmpeg_write_video

from src.gpxutil.core.config import CONFIG_HANDLER
from src.gpxutil.models.region import Region, get_default_languages, get_field_suffix
from src.gpxutil.models.road import IndonesiaRoad
from .svg_gen import generate_way_num_pad, generate_expwy_pad

chinese_font_path = CONFIG_HANDLER.config.video_info_layer.font_path.chinese
chinese_font_index = CONFIG_HANDLER.config.video_info_layer.font_path.chinese_index
english_font_path = CONFIG_HANDLER.config.video_info_layer.font_path.english
compass_img_path = CONFIG_HANDLER.config.video_info_layer.img_path.compass
route_time_sep_img_path = CONFIG_HANDLER.config.video_info_layer.img_path.route_time_sep
try:
    small_font = ImageFont.truetype(english_font_path, 48)
except IOError:
    print("字体无法加载，请检查路径和字体是否存在。")
    exit()
try:
    big_eng_font = ImageFont.truetype(english_font_path, 64)
except IOError:
    print("字体无法加载，请检查路径和字体是否存在。")
    exit()

font_color = '#FFFFFF'
image_size = (3840, 2160)
# 左中
# road_xy = (1280, 1988)
road_xy = (1464, 1988)
# 路牌尺寸仍用模块级常量；文本行的 y 坐标与字号由配置 frame.area.lines / frame.road.lines 提供
road_sign_width = 126
road_sign_height = 128
road_sign_space = 24
road_sign_char_space = 48

# 字体加载缓存：多行渲染按行字号创建字体，避免每行重复加载字体文件
_font_cache = {}


def _get_font(font_path, font_size, font_index=0):
    """带缓存的字体加载：同一 (字体路径, 字号, 索引) 只加载一次"""
    key = (font_path, font_size, font_index)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(font_path, font_size, font_index)
    return _font_cache[key]


def _get_line_font(line_index, font_size):
    """按行选择字体：第 0 行为主语言（中文），其余行为副语言（英文），字号取该行配置

    注意：行号是文本行列表过滤空行后的序号。若主语言文本缺失被剔除，次级语言会顶到
    第 0 行而按中文渲染；现有语言配置下主语言恒为 zh，不会出现该情况。
    """
    if line_index == 0:
        return _get_font(chinese_font_path, font_size, chinese_font_index)
    return _get_font(english_font_path, font_size)


# 导入期预热主语言中文字体（64 号）：中文字体缺失则启动即报错（沿用历史行为），且只加载一次
try:
    _get_font(chinese_font_path, 64, chinese_font_index)
except IOError:
    print("字体无法加载，请检查路径和字体是否存在。")
    exit()


def calc_line_positions(texts, lines, bottom_y, gap):
    """自下而上排列文本行位置。

    最后一行锚定 bottom_y，其余行按各自实际渲染占位高度（ascent+descent，中文
    明显高于副语言）向上堆叠，相邻行间留 gap 空隙。行数增减时上方行（含主语言
    中文行）自然上下移动，最后一行位置恒定。
    :param texts: 文本行列表（已过滤空行）
    :param lines: 配置行列表（取前 len(texts) 行，只消费 font_size）
    :param bottom_y: 最后一行文本的顶部 y
    :param gap: 相邻行的视觉空隙
    :return: (tops, fonts)：tops[i] 为第 i 行顶部 y，fonts[i] 为第 i 行字体（供绘制复用）
    """
    if not texts:
        return [], []
    fonts = [_get_line_font(i, line.font_size) for i, line in enumerate(lines[:len(texts)])]
    heights = [sum(font.getmetrics()) for font in fonts]
    tops = [0] * len(texts)
    tops[-1] = bottom_y
    for i in range(len(texts) - 2, -1, -1):
        tops[i] = tops[i + 1] - gap - heights[i]
    return tops, fonts

# compass_xy = (2248, 1924)
compass_xy = (2432, 1924)

# used_route_xy = (2796, 1924)
# 右上
used_route_xy = (2978, 1924)
# used_time_xy = (2796, 1997)
# 右上
used_time_xy = (2978, 1997)
time_route_width = 182
route_time_sep_xy = (3002, 1924)
remain_route_xy = (3117, 1924)
remain_time_xy = (3117, 1997)

# 右上
altitude_xy = (3483, 1924)
# 右上
altitude_unit_xy = (3483, 1997)

# 右上
speed_xy = (3649, 1924)
# 右上
speed_unit_xy = (3649, 1997)

# 缓存 SVG 信息，加快路牌生成速度
road_num_svg_cache = {}


def svg_to_img(svg_path):
    svg = cairosvg.svg2png(url=svg_path, dpi=72)
    return Image.open(io.BytesIO(svg))


def svg_drawing_to_img(svg_drawing: Drawing):
    svg = cairosvg.svg2png(bytestring=svg_drawing.tostring(), dpi=72)
    return Image.open(io.BytesIO(svg))


def build_area_texts(row: dict, region: Region) -> list[str]:
    """按语言集组装区域文本行：[主语言, 副语言...]，空行剔除"""
    primary, secondary = get_default_languages(region)
    texts = []
    # 主语言 zh：空格正序拼接
    if primary == 'zh':
        texts.append(' '.join([i for i in [row['province'], row['city'], row['area']] if i]))
    else:
        texts.append(', '.join([i for i in [row[f'area{get_field_suffix(primary)}'],
                                            row[f'city{get_field_suffix(primary)}'],
                                            row[f'province{get_field_suffix(primary)}']] if i]))
    # 副语言：逗号倒序拼接（同现状英文语序）
    for lang in secondary:
        text = ', '.join([i for i in [row[f'area{get_field_suffix(lang)}'],
                                      row[f'city{get_field_suffix(lang)}'],
                                      row[f'province{get_field_suffix(lang)}']] if i])
        texts.append(text)
    return [t for t in texts if t]


def build_road_texts(row: dict, region: Region) -> list[str]:
    """按语言集组装路名文本行：[主语言, 副语言...]，空行剔除"""
    primary, secondary = get_default_languages(region)
    langs = [primary] + secondary
    texts = [row[f'road_name{get_field_suffix(lang)}'] or '' for lang in langs]
    return [t for t in texts if t]


def parse_road_signs(row: dict, region: Region) -> list[Drawing]:
    """按 Region 解析 road_num 为路牌 Drawing 列表（沿用 road_num_svg_cache 缓存）"""
    road_num = row.get('road_num') or ''
    if not road_num:
        return []
    sign_list = []
    for road_sign in road_num.split(','):
        if road_sign in road_num_svg_cache:
            sign_list.append(road_num_svg_cache[road_sign])
            continue
        if region == Region.ID:
            road = IndonesiaRoad(road_sign, row.get('road_name'),
                                 [row.get('province_id'), row.get('province')])
            drawing = road.to_svg() if road.have_sign else None
        else:
            # 中国现状逻辑
            # 第一位为大写字母，则为国道、省道等普通道路，或者是国家高速
            if road_sign[0] in string.ascii_uppercase:
                if len(road_sign) == 4:
                    drawing = generate_way_num_pad(road_sign)
                else:
                    drawing = generate_expwy_pad(road_sign)
            # 否则为省级高速，从第一位读省简称
            else:
                drawing = generate_expwy_pad(road_sign[1:], province=road_sign[0])
        if drawing is not None:
            road_num_svg_cache[road_sign] = drawing
            sign_list.append(drawing)
    return sign_list


def generate_pic(area_texts, road_texts, road_sign_list, compass_angle, used_route, used_time,
                 remain_route, remain_time, altitude, speed):
    """
    根据信息生成信息图
    :param area_texts: 区域文本行列表，[0]=主语言（大字），[1:]=副语言（小字）
    :param road_texts: 路名文本行列表，同上
    :param road_sign_list: 当前道路编号标牌的 SVG 列表，如 [generate_way_num_pad('G310'), generate_way_num_pad('S209'), generate_expwy_pad('S0211', '豫')]
    :param compass_angle: 指南针角度
    :param used_route: 已走路程
    :param used_time: 已用时间
    :param remain_route: 剩余路程
    :param remain_time: 剩余时间
    :param altitude: 海拔
    :param speed: 速度
    :return: image

    区域与路名均按 [0]=主语言（中文大字）、[1:]=副语言（小字）逐行与配置行 zip 配对渲染；
    配置行数须不小于文本行数，超出配置的文本行会被截断不绘制。
    """
    image = Image.new(mode='RGBA', size=image_size)
    draw_table = ImageDraw.Draw(im=image)

    # 当前区域：主语言大字 + 副语言小字逐行，行坐标自下而上按实际文本高度堆叠（见 calc_line_positions）
    area_cfg = CONFIG_HANDLER.config.video_info_layer.frame.area
    area_tops, area_fonts = calc_line_positions(area_texts, area_cfg.lines, area_cfg.bottom_y, area_cfg.line_gap)
    for i, (text, line) in enumerate(zip(area_texts, area_cfg.lines)):
        line_x = line.x if line.x is not None else 0
        draw_table.text(xy=(line_x, area_tops[i]), text=text, fill=font_color, font=area_fonts[i])

    # 当前道路
    # road_sign_list = [generate_way_num_pad('G310'), generate_way_num_pad('S209'), generate_expwy_pad('S0211', '豫')]
    road_sign_offset = road_xy[0]
    if road_sign_list:
        road_sign_img_list = [svg_drawing_to_img(i) for i in road_sign_list]
        for i, road_sign_img in enumerate(road_sign_img_list):
            # 固定高度，等比例缩放，高为 road_sign_height
            new_road_sign_width = int(road_sign_img.size[0] * road_sign_height / road_sign_img.size[1])
            resized_img = road_sign_img.resize((new_road_sign_width, road_sign_height))
            # resized_img = road_sign_img.resize((road_sign_width, int(road_sign_img.size[1] * road_sign_width / road_sign_img.size[0])))
            image.paste(resized_img, (road_sign_offset, road_xy[1] - resized_img.size[1] // 2))
            road_sign_offset += new_road_sign_width + road_sign_space
        road_sign_offset = road_sign_offset - road_sign_space + road_sign_char_space
    # 路名：主语言大字 + 副语言小字逐行，行坐标自下而上按实际文本高度堆叠，x 沿用路牌起始 offset
    road_cfg = CONFIG_HANDLER.config.video_info_layer.frame.road
    road_tops, road_fonts = calc_line_positions(road_texts, road_cfg.lines, road_cfg.bottom_y, road_cfg.line_gap)
    max_right_x = road_sign_offset
    for i, (text, line) in enumerate(zip(road_texts, road_cfg.lines)):
        font = road_fonts[i]
        draw_table.text(xy=(road_sign_offset, road_tops[i]), text=text, fill=font_color, font=font)
        # 记录所有文本行的右边界，后续判断是否移动指南针位置
        right_x = road_sign_offset + draw_table.textlength(text=text, font=font)
        max_right_x = max(max_right_x, right_x)

    compass_final_xy = compass_xy
    if max_right_x + road_sign_char_space > compass_xy[0]:
        compass_final_xy = (math.ceil(max_right_x + road_sign_char_space), compass_xy[1])

    # 指南针
    if compass_angle is not None:
        compass_image = svg_to_img(compass_img_path)
        # 表示的是在当前方向上的正北（当前方向恒定为上），故不要加负号
        compass_image = compass_image.rotate(compass_angle, expand=False)
        image.paste(compass_image, compass_final_xy)

    # 已走 / 剩余
    if used_route is not None or used_time is not None or remain_route is not None or remain_time is not None:
        sep_image = svg_to_img(route_time_sep_img_path)
        image.paste(sep_image, route_time_sep_xy)
    if used_route is not None:
        # used_route_str 格式化 used_route 为一位小数
        used_route_str = '{:.1f}'.format(used_route)
        used_route_width = draw_table.textlength(text=used_route_str, font=big_eng_font)
        draw_table.text(xy=(used_route_xy[0] - used_route_width, used_route_xy[1]), text=used_route_str,
                        fill=font_color,
                        font=big_eng_font)
    if used_time is not None:
        # used_time_str: 格式化 used_time 秒数为时分秒
        used_time_str = '{:02d}:{:02d}:{:02d}'.format(int(used_time / 3600), int(used_time % 3600 / 60),
                                                      int(used_time % 60))
        used_time_width = draw_table.textlength(text=used_time_str, font=small_font)
        draw_table.text(xy=(used_time_xy[0] - used_time_width, used_time_xy[1]), text=used_time_str, fill=font_color,
                        font=small_font)
    if remain_route is not None:
        remain_route_str = '{:.1f}'.format(remain_route)
        draw_table.text(xy=remain_route_xy, text=remain_route_str, fill=font_color, font=big_eng_font)
    if remain_time is not None:
        remain_time_str = '{:02d}:{:02d}:{:02d}'.format(int(remain_time / 3600), int(remain_time % 3600 / 60),
                                                        int(remain_time % 60))
        draw_table.text(xy=remain_time_xy, text=remain_time_str, fill=font_color, font=small_font)

    # 高度
    if altitude is not None:
        altitude_str = '{:.1f}'.format(altitude)
        altitude_width = draw_table.textlength(text=altitude_str, font=big_eng_font)
        altitude_unit_width = draw_table.textlength(text='m', font=small_font)
        draw_table.text(xy=(altitude_xy[0] - altitude_width, altitude_xy[1]), text=altitude_str, fill=font_color,
                        font=big_eng_font)
        draw_table.text(xy=(altitude_unit_xy[0] - altitude_unit_width, altitude_unit_xy[1]), text='m', fill=font_color,
                        font=small_font)

    # 时速
    if speed is not None:
        speed_text = '{:.1f}'.format(speed)
        speed_width = draw_table.textlength(text=speed_text, font=big_eng_font)
        speed_unit_width = draw_table.textlength(text='km/h', font=small_font)
        draw_table.text(xy=(speed_xy[0] - speed_width, speed_xy[1]), text=speed_text, fill=font_color,
                        font=big_eng_font)
        draw_table.text(xy=(speed_unit_xy[0] - speed_unit_width, speed_unit_xy[1]), text='km/h', fill=font_color,
                        font=small_font)

    return image
    # image.show()  # 直接显示图片
    # # image.save('满月.png', 'PNG')  # 保存在当前路径下，格式为PNG
    # image.close()


def read_csv(path: str) -> List[dict]:
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


def fill_missing_entries(data):
    """
    填充 List[dict] 中 'elapsed_time' 不连续导致的缺失项。
    :param data: 包含字典的列表，每个字典至少包含 'elapsed_time' 键。
    :return: 'elapsed_time' 连续的新列表。
    """
    if not data:
        return []

    # 找出 'elapsed_time' 的最小值和最大值
    min_time = min(item['elapsed_time'] for item in data)
    max_time = max(item['elapsed_time'] for item in data)

    # 创建一个映射表，方便快速查找
    time_to_data = {item['elapsed_time']: item for item in data}

    # 准备结果列表
    filled_data = []

    # 上一个处理的字典，用于填充缺失项的其他键值对
    last_item = None

    for elapsed_time in tqdm(range(min_time, max_time + 1), total=max_time - min_time + 1,
                             desc='Filling missing entries', unit='point(s)'):
        if elapsed_time in time_to_data:
            filled_data.append(time_to_data[elapsed_time])
            last_item = time_to_data[elapsed_time]
        else:
            # 如果发现不连续，使用上一个字典的内容创建一个新的字典
            new_item = last_item.copy() if last_item else {}
            new_item['elapsed_time'] = elapsed_time
            filled_data.append(new_item)

    return filled_data


# 整理字典数据，读到附加信息
def read_csv_with_additional_info(
        path: str, start_index=0, end_index=-1,
        start_index_after_fill=0, end_index_after_fill=-1,
        crop_start=0, crop_end=-1,
        region: Region = Region.CN
):
    """
    整理字典数据，读到附加信息
    :param path: CSV 文件路径
    :param start_index: 开始的序号
    :param end_index: 结束的序号
    :param start_index_after_fill: 填补缺失帧之后的开始的序号（用于与视频对齐，填写秒数）
    :param end_index_after_fill: 填补缺失帧之后的结束的序号（用于与视频对齐，填写秒数）
    :param crop_start 输出帧的序号起始，用于修改特定范围内的帧
    :param crop_end 输出帧的序号结束，用于修改特定范围内的帧
    :param region 道路编号解析与多语言文本的地区体系，默认中国大陆
    :return: 整理好的字典数据
    """
    dict_list = read_csv(path)
    # start_index / end_index 对应 CSV 的 index 列（闭区间），而不是行位置切片；
    # index 列存在跳变时行位置与 index 值不一致
    if start_index > 0 or end_index >= 0:
        dict_list = [row for row in dict_list
                     if int(row['index']) >= start_index
                     and (end_index < 0 or int(row['index']) <= end_index)]
    dict_list = fill_missing_entries(dict_list)
    # start_index_after_fill / end_index_after_fill 是填补缺失帧后的行位置区间；
    # end_index_after_fill 为 -1 时表示到最后（直接 [: -1] 会丢掉最后一行）
    if start_index_after_fill > 0 or end_index_after_fill >= 0:
        end = end_index_after_fill if end_index_after_fill >= 0 else len(dict_list)
        dict_list = dict_list[start_index_after_fill:end]
    new_dict_list = []
    total_time = dict_list[-1]['elapsed_time'] - dict_list[0]['elapsed_time']
    total_distance = dict_list[-1]['distance'] - dict_list[0]['distance']
    for i, row in tqdm(enumerate(dict_list), total=len(dict_list), desc='Processing dict', unit='point(s)'):
        new_row = row.copy()
        # crop_end 为 -1 时表示不裁剪；旧的 len 近似在 index 列跳变时会误裁尾部行
        if int(row['index']) < crop_start or (crop_end >= 0 and int(row['index']) > crop_end):
            continue
        new_row['real_index'] = i
        new_row['elapsed_time'] = row['elapsed_time'] - dict_list[0]['elapsed_time'] - start_index_after_fill if row[
                                                                                                                     'elapsed_time'] is not None else None
        new_row['distance'] = row['distance'] - dict_list[0]['distance'] if row['distance'] is not None else None
        new_row['remain_time'] = total_time - new_row['elapsed_time'] if new_row['elapsed_time'] is not None else None
        new_row['remain_distance'] = total_distance - new_row['distance'] if new_row['distance'] is not None else None
        # 单位调整
        new_row['speed'] = new_row['speed'] * 3.6 if new_row['speed'] is not None else None
        new_row['distance'] = new_row['distance'] / 1000 if new_row['distance'] is not None else None
        new_row['remain_distance'] = new_row['remain_distance'] / 1000 if new_row[
                                                                              'remain_distance'] is not None else None
        # 区域与路名按语言集组装多行文本，区域信息如无则不显示；路牌按 Region 解析
        new_row['area_texts'] = build_area_texts(row, region)
        new_row['road_texts'] = build_road_texts(row, region)
        new_row['road_sign_svg'] = parse_road_signs(row, region)
        new_dict_list.append(new_row)
    return new_dict_list


def generate_pic_from_processed_dict_list(dict_list: List[dict], crop_start=0, out_dir: str = 'out/test', max_workers=4):
    """
    通过调整后的字典列表生成图片（多线程版本）
    :param dict_list: 字典列表
    :param crop_start: 裁剪开始。注意：这里看的是 real_index 键的值
    :param out_dir: 输出目录。末尾不带斜杠
    :param max_workers: 最大线程数
    :return:
    """
    def process_row(i, row):
        img = generate_pic(
            area_texts=row['area_texts'], road_texts=row['road_texts'],
            road_sign_list=row['road_sign_svg'],
            compass_angle=row['course'],
            used_route=row['distance'], used_time=row['elapsed_time'],
            remain_route=row['remain_distance'], remain_time=row['remain_time'],
            altitude=row['elevation'], speed=row['speed']
        )
        img.save(f'{out_dir}/pic_{row["real_index"]:08d}.png', 'PNG')
        img.close()


    # 多线程处理时内存泄漏问题严重
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_row, i, row) for i, row in enumerate(dict_list)]
        # 取 result 以向上抛出工作线程中的异常，避免被静默吞掉
        for future in tqdm(as_completed(futures), total=len(futures), desc='Generating pic', unit='point(s)'):
            future.result()
    # for i, row in enumerate(tqdm(dict_list, desc='Generating pic', unit='point(s)')):
    #     process_row(i, row)
    #     # 每处理完一张图片就进行垃圾回收
    #     gc.collect()

def generate_pic_from_csv(path: str, start_index=0, end_index=-1, start_index_after_fill=0, end_index_after_fill=-1,
                          crop_start=0, crop_end=-1, out_dir: str = 'out/test', region: Region = Region.CN):
    """
    从 CSV 文件中生成图片
    :param path: CSV 文件路径
    :param start_index: 开始的序号
    :param end_index: 结束的序号
    :param start_index_after_fill: 填补缺失帧之后的开始的序号（用于与视频对齐，填写秒数）
    :param end_index_after_fill: 填补缺失帧之后的结束的序号（用于与视频对齐，填写秒数）
    :param crop_start 输出帧的序号起始，用于修改特定范围内的帧
    :param crop_end 输出帧的序号结束，用于修改特定范围内的帧
    :param out_dir: 输出目录。末尾不带斜杠
    :param region: 道路编号解析与多语言文本的地区体系，默认中国大陆
    :return: None
    """
    dict_list = read_csv_with_additional_info(path, start_index, end_index, start_index_after_fill,
                                              end_index_after_fill, crop_start, crop_end, region=region)
    generate_pic_from_processed_dict_list(dict_list, crop_start, out_dir)


# def generate_video_from_pics(from_path: str, gen_path: str):
#     imglist = []
#     for file_name in sorted(os.listdir(from_path)):
#         if file_name.endswith('.png'):
#             imglist.append(os.path.join(from_path, file_name))
#
#     clip = moviepy.ImageSequenceClip(imglist, fps=1, with_mask=True, is_mask=False)  # 这里参数似乎没用
#     ffmpeg_write_video(clip, gen_path, fps=1, codec="qtrle", pixel_format="rgba")

# # 将 PIL.Image 对象转换为 NumPy 数组
# def image_to_array(image):
#     return np.array(image)

# def images_to_video(images: list[Image], output_path, fps=1):
#     # 获取图像尺寸
#     frame_size = images[0].size
#
#     # 将所有 PIL.Image 对象转换为 NumPy 数组
#     image_arrays = [image_to_array(image) for image in images]
#
#     # 使用 imageio 写入视频
#     imageio.mimsave(output_path, image_arrays, fps=fps, output_params=['-vcodec', 'qtrle', '-pix_fmt', 'rgba'])

if __name__ == '__main__':
    # img = generate_pic(
    #     area_texts=['河南省 三门峡市 渑池县', 'Mianchi County, Sanmenxia City, Henan Province'],
    #     road_texts=['黄河路', 'Huanghe Rd.'],
    #     # road_sign_list=[generate_way_num_pad('G310')],
    #     road_sign_list=None,
    #     compass_angle=233,
    #     used_route=20.8, used_time='0:24:25',
    #     remain_route=45.2, remain_time='1:23:24',
    #     altitude=1000, speed=50
    # )
    # img.show()
    # img.close()
    # processed_point_info = read_csv_with_additional_info('test/20250226132250.csv')[1421]
    # print(processed_point_info)
    # img = generate_pic(
    #     area_texts=processed_point_info['area_texts'], road_texts=processed_point_info['road_texts'],
    #     # road_sign_list=[generate_way_num_pad('G310')],
    #     road_sign_list=processed_point_info['road_sign_svg'],
    #     compass_angle=processed_point_info['course'],
    #     used_route=processed_point_info['distance'], used_time=processed_point_info['elapsed_time'],
    #     remain_route=processed_point_info['remain_distance'], remain_time=processed_point_info['remain_time'],
    #     altitude=processed_point_info['elevation'], speed=processed_point_info['speed']
    # )
    # img.show()
    # img.close()
    pic_list = generate_pic_from_csv(r'E:\project\recorded\route\gcj\九江-景德镇.csv',
                                     out_dir=r"E:\project\recorded\20250409-九江-景德镇\overlay\2", crop_start=6379,
                                     crop_end=6475)
    # 生成视频在 Pr 中有问题，故只做图像序列
    # generate_video_from_pics('out/test/', 'out/test.mov')