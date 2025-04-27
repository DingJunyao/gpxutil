from xml.dom.minidom import parse
import codecs
from tqdm import tqdm

import sys
from pathlib import Path

from vendor.coordTransform_py.coordTransform_utils import wgs84_to_gcj02, wgs84_to_bd09, gcj02_to_wgs84, gcj02_to_bd09, \
    bd09_to_wgs84, bd09_to_gcj02

# 将 vendor/coordTransform_py 添加到 Python 路径
vendor_path = str(Path(__file__).parent.parent.parent.parent / "vendor" / "coordTransform_py")
sys.path.insert(0, vendor_path)

from vendor.coordTransform_py.coord_converter import convert_by_type

def convert_single_point(lng, lat, original_coordinate_type, transformed_coordinate_type):
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

def convert_gpx(path, out_path, convert_type, lng_column='lon', lat_column='lat'):
    domTree = parse(path)
    # 文档根元素
    gpxNode = domTree.documentElement
    trkptNode = gpxNode.getElementsByTagName("trkpt")

    for trkpt in tqdm(trkptNode, total=len(trkptNode), desc='Converting GPX points', unit='point(s)'):
        result = convert_by_type(float(trkpt.attributes[lng_column].value), float(trkpt.attributes[lat_column].value), convert_type)
        trkpt.attributes[lng_column].value=str(result[0])
        trkpt.attributes[lat_column].value=str(result[1])

    with open(out_path, 'wb+') as f:
        #解决写入中文乱码问题
        f = codecs.lookup("utf-8")[3](f)
        domTree.writexml(f, encoding='utf-8')

if __name__ == '__main__':
    convert_gpx(r'E:\project\recorded\route\20250411104616.gpx', 'gcj.gpx', 'w2g')