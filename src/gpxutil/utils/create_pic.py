import csv
import io
import os
import string
from datetime import datetime
from typing import List

import cairosvg
import moviepy
from PIL import Image, ImageDraw, ImageFont
from svgwrite import Drawing
from tqdm import tqdm

import numpy as np
import imageio

from moviepy.video.io.ffmpeg_writer import ffmpeg_write_video

from svg_gen import generate_way_num_pad, generate_expwy_pad

chinese_font_path = "../../../asset/font/SourceHanSans_static_super_otc.ttc"
english_font_path = "../../../asset/font/SourceSans3-Regular.otf"
compass_img_path = "../../../asset/compass.svg"
route_time_sep_img_path = "../../../asset/route_time_sep.svg"
try:
    big_font = ImageFont.truetype(chinese_font_path, 64, 12)
except IOError:
    print("字体无法加载，请检查路径和字体是否存在。")
    exit()
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
# 无特殊标注均为左上
area_chinese_xy = (191.8085, 1924)
area_english_xy = (192, 1997)
# 左中
# road_xy = (1280, 1988)
road_xy = (1464, 1988)
road_sign_width = 126
road_sign_height = 128
road_sign_space = 24
road_sign_char_space = 48
road_chinese_y = 1924
road_english_y = 1997

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

def generate_pic(
        area_zh, area_en, road_sign_list, road_zh, road_en, compass_angle, used_route, used_time, remain_route,
        remain_time, altitude, speed
):
    """
    根据信息生成信息图
    :param area_zh: 中文区域名
    :param area_en: 英文区域名
    :param road_sign_list: 当前道路编号标牌的 SVG 列表，如 [generate_way_num_pad('G310'), generate_way_num_pad('S209'), generate_expwy_pad('S0211', '豫')]
    :param road_zh: 中文路名
    :param road_en: 英文路名
    :param compass_angle: 指南针角度
    :param used_route: 已走路程
    :param used_time: 已用时间
    :param remain_route: 剩余路程
    :param remain_time: 剩余时间
    :param altitude: 海拔
    :param speed: 速度
    :return: image
    """
    image = Image.new(mode='RGBA', size=image_size)
    draw_table = ImageDraw.Draw(im=image)

    # 当前区域
    if area_zh:
        draw_table.text(xy=area_chinese_xy, text=area_zh, fill=font_color, font=big_font)
    if area_en:
        draw_table.text(xy=area_english_xy, text=area_en, fill=font_color, font=small_font)
    
    # 当前道路
    # road_sign_list = [generate_way_num_pad('G310'), generate_way_num_pad('S209'), generate_expwy_pad('S0211', '豫')]
    road_sign_offset = road_xy[0]
    if road_sign_list:
        road_sign_img_list = [svg_drawing_to_img(i) for i in road_sign_list]
        for i, road_sign_img in enumerate(road_sign_img_list):
            # 固定高度，等比例缩放，高为 road_sign_height
            new_road_sign_wigth = int(road_sign_img.size[0] * road_sign_height / road_sign_img.size[1])
            resized_img = road_sign_img.resize((new_road_sign_wigth, road_sign_height))
            # resized_img = road_sign_img.resize((road_sign_width, int(road_sign_img.size[1] * road_sign_width / road_sign_img.size[0])))
            image.paste(resized_img, (road_sign_offset, road_xy[1] - resized_img.size[1] // 2))
            road_sign_offset += new_road_sign_wigth + road_sign_space
        road_sign_offset = road_sign_offset - road_sign_space + road_sign_char_space
    if road_zh:
        draw_table.text(xy=(road_sign_offset, road_chinese_y), text=road_zh, fill=font_color, font=big_font)
    if road_en:
        draw_table.text(xy=(road_sign_offset, road_english_y), text=road_en, fill=font_color, font=small_font)
    
    # 指南针
    if compass_angle is not None:
        compass_image = svg_to_img(compass_img_path)
        # 表示的是在当前方向上的正北（当前方向恒定为上），故不要加负号
        compass_image = compass_image.rotate(compass_angle, expand=False)
        image.paste(compass_image, compass_xy)
    
    # 已走 / 剩余
    if used_route is not None or used_time is not None or remain_route is not None or remain_time is not None:
        sep_image = svg_to_img(route_time_sep_img_path)
        image.paste(sep_image, route_time_sep_xy)
    if used_route is not None:
        # used_route_str 格式化 used_route 为一位小数
        used_route_str = '{:.1f}'.format(used_route)
        used_route_width = draw_table.textlength(text=used_route_str, font=big_eng_font)
        draw_table.text(xy=(used_route_xy[0] - used_route_width, used_route_xy[1]), text=used_route_str, fill=font_color,
                        font=big_eng_font)
    if used_time is not None:
        # used_time_str: 格式化 used_time 秒数为时分秒
        used_time_str = '{:02d}:{:02d}:{:02d}'.format(int(used_time / 3600), int(used_time % 3600 / 60), int(used_time % 60))
        used_time_width = draw_table.textlength(text=used_time_str, font=small_font)
        draw_table.text(xy=(used_time_xy[0] - used_time_width, used_time_xy[1]), text=used_time_str, fill=font_color, font=small_font)
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
        draw_table.text(xy=(altitude_xy[0] - altitude_width, altitude_xy[1]), text=altitude_str, fill=font_color, font=big_eng_font)
        draw_table.text(xy=(altitude_unit_xy[0] - altitude_unit_width, altitude_unit_xy[1]), text='m', fill=font_color, font=small_font)
    
    # 时速
    if speed is not None:
        speed_text = '{:.1f}'.format(speed)
        speed_width = draw_table.textlength(text=speed_text, font=big_eng_font)
        speed_unit_width = draw_table.textlength(text='km/h', font=small_font)
        draw_table.text(xy=(speed_xy[0] - speed_width, speed_xy[1]), text=speed_text, fill=font_color, font=big_eng_font)
        draw_table.text(xy=(speed_unit_xy[0] - speed_unit_width, speed_unit_xy[1]), text='km/h', fill=font_color, font=small_font)

    return image
    # image.show()  # 直接显示图片
    # # image.save('满月.png', 'PNG')  # 保存在当前路径下，格式为PNG
    # image.close()

def read_csv(path: str) -> List[dict]:
    dict_list = []
    with open(path, mode='r', newline='', encoding='gbk') as csv_file:
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
                    row[key] = int(value)
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

    for elapsed_time in tqdm(range(min_time, max_time + 1), total=max_time - min_time + 1, desc='Filling missing entries', unit='point(s)'):
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
        path: str, start_index = 0, end_index = -1,
        start_index_after_fill = 0, end_index_after_fill = -1,
        crop_start = 0, crop_end = -1
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
    :return: 整理好的字典数据
    """
    global road_num_svg_cache
    dict_list = read_csv(path)[start_index:end_index]
    dict_list = fill_missing_entries(dict_list)[start_index_after_fill:end_index_after_fill]
    new_dict_list = []
    total_time = dict_list[-1]['elapsed_time'] - dict_list[0]['elapsed_time']
    total_distance = dict_list[-1]['distance'] - dict_list[0]['distance']
    if crop_end < 0:
        crop_end += len(dict_list)
    for i, row in tqdm(enumerate(dict_list), total=len(dict_list), desc='Processing dict', unit='point(s)'):
        if int(row['index']) < crop_start or int(row['index']) > crop_end:
            continue
        row['real_index'] = i
        row['elapsed_time'] = row['elapsed_time'] - dict_list[0]['elapsed_time'] if row['elapsed_time'] is not None else None
        row['distance'] = row['distance'] - dict_list[0]['distance'] if row['distance'] is not None else None
        row['remain_time'] = total_time - row['elapsed_time'] if row['elapsed_time'] is not None else None
        row['remain_distance'] = total_distance - row['distance'] if row['distance'] is not None else None
        # 单位调整
        row['speed'] = row['speed'] * 3.6 if row['speed'] is not None else None
        row['distance'] = row['distance'] / 1000 if row['distance'] is not None else None
        row['remain_distance'] = row['remain_distance'] / 1000 if row['remain_distance'] is not None else None
        row['full_area'] = f"{row['province']} {row['city']} {row['area']}"
        row['full_area_en'] = f"{row['area_en']}, {row['city_en']}, {row['province_en']}"
        row['road_sign_svg'] = []
        if 'road_num' in row and row['road_num']:
            road_sign_num_list = row['road_num'].split(',')
            for road_sign in road_sign_num_list:
                if road_sign in road_num_svg_cache:
                    row['road_sign_svg'].append(road_num_svg_cache[road_sign])
                    continue
                # 第一位为大写字母，则为国道、省道等普通道路，或者是国家高速
                if road_sign[0] in string.ascii_uppercase:
                    if len(road_sign) == 4:
                        svg_drawing = generate_way_num_pad(road_sign)
                    else:
                        svg_drawing = generate_expwy_pad(road_sign)
                # 否则为省级高速，从第一位读省简称
                else:
                    svg_drawing = generate_expwy_pad(road_sign[1:], province=road_sign[0])
                road_num_svg_cache[road_sign] = svg_drawing
                row['road_sign_svg'].append(svg_drawing)
        new_dict_list.append(row)
    return new_dict_list

def generate_pic_from_processed_dict_list(dict_list: List[dict], crop_start = 0):
    """
    通过调整后的字典列表生成图片
    :param dict_list: 字典列表
    :param crop_start: 裁剪开始。注意：这里看的是 real_index 键的值
    :return:
    """
    for i, row in tqdm(enumerate(dict_list), total=len(dict_list), desc='Generating pic', unit='point(s)'):
        img = generate_pic(
            area_zh=row['full_area'], area_en=row['full_area_en'],
            # road_sign_list=[generate_way_num_pad('G310')],
            road_sign_list=row['road_sign_svg'],
            road_zh=row['road_name'], road_en=row['road_name_en'],
            compass_angle=row['course'],
            used_route=row['distance'], used_time=row['elapsed_time'],
            remain_route=row['remain_distance'], remain_time=row['remain_time'],
            altitude=row['elevation'], speed=row['speed']
        )
        # img.show()
        img.save('out/test/pic_{:0>8d}.png'.format(row['real_index']), 'PNG')
        img.close()
    # return img_list

def generate_pic_from_csv(path: str, start_index = 0, end_index = -1, start_index_after_fill = 0, end_index_after_fill = -1, crop_start = 0, crop_end = -1):
    dict_list = read_csv_with_additional_info(path, start_index, end_index, start_index_after_fill, end_index_after_fill, crop_start, crop_end)
    generate_pic_from_processed_dict_list(dict_list, crop_start)

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
    #     area_zh='河南省 三门峡市 渑池县', area_en='Mianchi County, Sanmenxia City, Henan Province',
    #     # road_sign_list=[generate_way_num_pad('G310')],
    #     road_sign_list=None,
    #     road_zh='黄河路', road_en='Huanghe Rd.',
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
    #     area_zh=processed_point_info['full_area'], area_en=processed_point_info['full_area_en'],
    #     # road_sign_list=[generate_way_num_pad('G310')],
    #     road_sign_list=processed_point_info['road_sign_svg'],
    #     road_zh=processed_point_info['road_name'], road_en=processed_point_info['road_name_en'],
    #     compass_angle=processed_point_info['course'],
    #     used_route=processed_point_info['distance'], used_time=processed_point_info['elapsed_time'],
    #     remain_route=processed_point_info['remain_distance'], remain_time=processed_point_info['remain_time'],
    #     altitude=processed_point_info['elevation'], speed=processed_point_info['speed']
    # )
    # img.show()
    # img.close()
    pic_list = generate_pic_from_csv('../../../test/20250226132250.csv', start_index_after_fill=0, end_index_after_fill=-17, crop_start=1342, crop_end=1358)
    # 生成视频在 Pr 中有问题，故只做图像序列
    # generate_video_from_pics('out/test/', 'out/test.mov')