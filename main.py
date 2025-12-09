import sqlite3

from geopandas import GeoDataFrame

from src.gpxutil.core.config import CONFIG_HANDLER
from src.gpxutil.models.route import Route
if CONFIG_HANDLER.config.area_info.gdf:
    from src.gpxutil.utils.db_connect import AreaCodeConnectHandler
    from src.gpxutil.utils.gdf_handler import GDFListHandler


def transform_route_info_from_gpx_file(
        input_gpx_file_path: str,
        output_transformed_gpx_file_path: str,
        output_csv_file_path: str,
        transform_coordinate: bool = True,
        coordinate_type: str = 'wgs84',
        transformed_coordinate_type: str = 'gcj02',
        set_area: bool = True,
        source: str = None,
        area_gdf_list: list[GeoDataFrame] = None,
        area_code_conn: sqlite3.Connection = None,
        export_transformed_coordinate: bool = True
):
    if set_area and (source == 'gdf' or (source is None and CONFIG_HANDLER.config.area_info.use == 'gdf')):
        if area_gdf_list is None:
            area_gdf_list = GDFListHandler().list
        if area_code_conn is None:
            area_code_conn = AreaCodeConnectHandler().conn
    """导入数据、转换、添加行政区划和道路名称"""
    route = Route.from_gpx_file(
        input_gpx_file_path,
        transform_coordinate=transform_coordinate, coordinate_type=coordinate_type, transformed_coordinate_type=transformed_coordinate_type,
        set_area=set_area, source=source, area_gdf_list=area_gdf_list, area_code_conn=area_code_conn
    )
    # Route.from_json_file('./test/gpx_sample/from_gps_logger_to_json.json')
    # Route.from_csv('./test/gpx_sample/from_gps_logger_to_csv.csv', coordinate_type='wgs84', transformed_coordinate_type='gcj02')

    """导出数据，供外部修改、生成轨迹"""
    route.to_gpx_file(output_transformed_gpx_file_path, export_transformed_coordinate=export_transformed_coordinate)
    route.to_csv(output_csv_file_path)
    # route.to_json_file('./test/gpx_sample/from_gps_logger_to_json.json')

if __name__ == '__main__':
    transform_route_info_from_gpx_file(
        './test/gpx_sample/from_gps_logger.gpx',
        './test/gpx_sample/from_gps_logger_to_gpx.gpx',
        './test/gpx_sample/from_gps_logger_to_csv_amap.csv'
    )
    """
    gdf:
        导入 353 条边界数据，13s
        处理 555 条 GPX 点，51s
        只有中文的省市区区划
    nominatim:
        处理 555 条 GPX 点，25s
    baidu:
        只有中文：处理 100 条 GPX 点，40s
        中英文：处理 50 条 GPX 点，40s
    amap：
        处理 555 条 GPX 点，4 min 34 s
    """