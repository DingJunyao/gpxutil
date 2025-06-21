import io
from typing import Literal, TextIO, IO
from concurrent.futures import ThreadPoolExecutor, as_completed
from xml.dom.minidom import parse, Document
import codecs
import sys
from pathlib import Path

from tqdm import tqdm

from src.gpxutil.utils.process import threaded_map
from vendor.coordTransform_py.coordTransform_utils import wgs84_to_gcj02, wgs84_to_bd09, gcj02_to_wgs84, gcj02_to_bd09, \
    bd09_to_wgs84, bd09_to_gcj02

# 将 vendor/coordTransform_py 添加到 Python 路径
vendor_path = str(Path(__file__).parent.parent.parent.parent / "vendor" / "coordTransform_py")
sys.path.insert(0, vendor_path)

from vendor.coordTransform_py.coord_converter import convert_by_type

coordinate_type_hint = Literal['wgs84', 'gcj02', 'bd09']

def convert_single_point(
        lng, lat,
        original_coordinate_type: coordinate_type_hint,
        transformed_coordinate_type: coordinate_type_hint
):
    if original_coordinate_type == transformed_coordinate_type:
        return lng, lat
    if original_coordinate_type == 'wgs84':
        if transformed_coordinate_type == 'gcj02':
            return wgs84_to_gcj02(float(lng), float(lat))
        if transformed_coordinate_type == 'bd09':
            return wgs84_to_bd09(float(lng), float(lat))
    elif original_coordinate_type == 'gcj02':
        if transformed_coordinate_type == 'wgs84':
            return gcj02_to_wgs84(float(lng), float(lat))
        if transformed_coordinate_type == 'bd09':
            return gcj02_to_bd09(float(lng), float(lat))
        return None
    elif original_coordinate_type == 'bd09':
        if transformed_coordinate_type == 'wgs84':
            return bd09_to_wgs84(float(lng), float(lat))
        if transformed_coordinate_type == 'gcj02':
            return bd09_to_gcj02(float(lng), float(lat))
        return None
    raise AttributeError('Invalid coordinate type')

def gen_convert_type(
        original_coordinate_type: coordinate_type_hint,
        transformed_coordinate_type: coordinate_type_hint
) -> str:
    """
    Generate convert type for vendor.coordTransform_py.coord_converter.convert_by_type.
    :param original_coordinate_type: str
    :param transformed_coordinate_type:
    :return:
    """
    if original_coordinate_type == transformed_coordinate_type:
        # return same file
        return ''
    if original_coordinate_type == 'wgs84':
        if transformed_coordinate_type == 'gcj02':
            return 'w2g'
        if transformed_coordinate_type == 'bd09':
            return 'w2b'
    elif original_coordinate_type == 'gcj02':
        if transformed_coordinate_type == 'wgs84':
            return 'g2w'
        if transformed_coordinate_type == 'bd09':
            return 'g2b'
    elif original_coordinate_type == 'bd09':
        if transformed_coordinate_type == 'wgs84':
            return 'b2w'
        if transformed_coordinate_type == 'gcj02':
            return 'b2g'
    raise AttributeError('Invalid coordinate type')

@threaded_map(desc="Converting GPX points", unit="point(s)")
def process_trkpt(trkpt, convert_type):
    result = convert_by_type(float(trkpt.attributes['lon'].value), float(trkpt.attributes['lat'].value), convert_type)
    trkpt.attributes['lon'].value = str(result[0])
    trkpt.attributes['lat'].value = str(result[1])
    return trkpt
def convert_gpx(
        file: str | IO,
        original_coordinate_type,
        transformed_coordinate_type,
) -> Document:

    convert_type = gen_convert_type(original_coordinate_type, transformed_coordinate_type)
    dom_tree = parse(file)
    if original_coordinate_type == transformed_coordinate_type:
        return dom_tree

    # 文档根元素
    gpx_node = dom_tree.documentElement
    trkpt_nodes = gpx_node.getElementsByTagName("trkpt")

    process_trkpt(trkpt_nodes, convert_type)

    return dom_tree


def convert_gpx_to_file(
        in_path,
        out_path,
        original_coordinate_type,
        transformed_coordinate_type,
):
    dom_tree = convert_gpx(in_path, original_coordinate_type, transformed_coordinate_type)

    with open(out_path, 'wb+') as f:
        #解决写入中文乱码问题
        f = codecs.lookup("utf-8")[3](f)
        dom_tree.writexml(f, encoding='utf-8')

if __name__ == '__main__':
    convert_gpx_to_file(r"E:\project\recorded\202504旅游轨迹\20250402083731.gpx", 'gcj.gpx', original_coordinate_type='wgs84', transformed_coordinate_type='gcj02')