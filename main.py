import argparse
import sqlite3
import string
import sys
import os
from geopandas import GeoDataFrame

from src.gpxutil.core.config import CONFIG_HANDLER
from src.gpxutil.models.route import Route
from src.gpxutil.utils.create_pic import generate_pic_from_csv
from src.gpxutil.utils.gen_road_info import gen_route_info, get_info, read_csv
from src.gpxutil.utils.svg_gen import generate_expwy_pad, generate_way_num_pad

if CONFIG_HANDLER.config.area_info.gdf:
    from src.gpxutil.utils.geocoding.gdf.db_connect import AreaCodeConnectHandler
    from src.gpxutil.utils.geocoding.gdf.gdf_handler import GDFListHandler
    from src.gpxutil.utils.geocoding.gdf.gdf_handler import load_area_gdf_list


def transform_route_info_from_gpx_file(
        input_gpx_file_path: str,
        output_transformed_gpx_file_path: str,
        output_csv_file_path: str,
        transform_coordinate: bool = True,
        coordinate_type: str = 'wgs84',
        transformed_coordinate_type: str = 'gcj02',
        set_area: bool = True,
        source: str = None,
        gdf_path: str = None,
        gdf_db_path: str = None,
        area_gdf_list: list[GeoDataFrame] = None,
        area_code_conn: sqlite3.Connection = None,
        export_transformed_coordinate: bool = True
):
    if set_area and (source == 'gdf' or (source is None and CONFIG_HANDLER.config.area_info.use == 'gdf')):
        # 如果提供了CLI参数，则使用CLI参数指定的路径
        if gdf_path is not None and gdf_db_path is not None:
            area_gdf_list = load_area_gdf_list(gdf_path)
            area_code_conn = sqlite3.connect(gdf_db_path)
        else:
            # 否则使用默认配置
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

    """导出数据，供外部修改、生成轨迹"""
    route.to_gpx_file(output_transformed_gpx_file_path, export_transformed_coordinate=export_transformed_coordinate)
    route.to_csv(output_csv_file_path)


def generate_road_info(input_csv_file_path: str):
    csv_dict_list = read_csv(input_csv_file_path)
    city_info_list = get_info(csv_dict_list)
    return gen_route_info(city_info_list)

def main():
    parser = argparse.ArgumentParser(description='GPX Utility Tool - Process GPX files and generate image sequences from CSV')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Subparser for GPX processing
    gpx_parser = subparsers.add_parser('transform', help='Process GPX file to generate transformed GPX and CSV')
    gpx_parser.add_argument('input', help='Input GPX file path')
    gpx_parser.add_argument('output_gpx', nargs='?', help='Output transformed GPX file path (optional)')
    gpx_parser.add_argument('output_csv', nargs='?', help='Output CSV file path (optional)')
    gpx_parser.add_argument('--no_transform_coordinate', action='store_false', help='不转换坐标')
    gpx_parser.add_argument('--no_set_area', action='store_false', help='不设置行政区划')
    gpx_parser.add_argument('--coordinate_type', default='wgs84', help='坐标类型，可选 wgs84 或 gcj02')
    gpx_parser.add_argument('--transformed_coordinate_type', default='gcj02', help='转换后坐标类型，可选 wgs84 或 gcj02')
    gpx_parser.add_argument('--area_source', choices=['nominatim', 'gdf', 'baidu', 'amap'], help='行政区划数据来源，可选 nominatim, gdf, baidu, amap')
    gpx_parser.add_argument('--gdf_path', help='GDF文件目录路径，仅当area_source为gdf时有效')
    gpx_parser.add_argument('--gdf_db_path', help='GDF数据库文件路径，仅当area_source为gdf时有效')

    pad_parser = subparsers.add_parser('pad', help='Generate SVG num pad')
    pad_parser.add_argument('code', help='road code (eg. G318， G30, G0102, 苏S88, S111)')
    pad_parser.add_argument('output_svg', nargs='?', help='Output SVG file path (optional)')
    pad_parser.add_argument('--name', nargs='?', help='name of the road (optional, only for expressway)')
    
    # Subparser for CSV to image sequence
    csv_parser = subparsers.add_parser('overlay', help='Generate image sequence from CSV file')
    csv_parser.add_argument('input', help='Input CSV file path')
    csv_parser.add_argument('output_dir', help='Output directory for image sequence')
    csv_parser.add_argument('--start_index', type=int, default=0, help='输出帧的索引起始。对应 CSV 文件的 index 列')
    csv_parser.add_argument('--end_index', type=int, default=-1, help='输出帧的索引结束。对应 CSV 文件的 index 列')
    csv_parser.add_argument('--start_index_after_fill', default=0, type=int, help='填补缺失帧之后的开始的序号（用于与视频对齐，填写秒数）')
    csv_parser.add_argument('--end_index_after_fill', default=-1, type=int, help='填补缺失帧之后的结束的序号（用于与视频对齐，填写秒数）')
    csv_parser.add_argument('--crop_start', type=int, default=0, help='输出帧的序号起始，用于修改特定范围内的帧。对应 CSV 文件的 index 列')
    csv_parser.add_argument('--crop_end', type=int, default=-1, help='输出帧的序号结束，用于修改特定范围内的帧。对应 CSV 文件的 index 列')

    # gen road info
    info_parser = subparsers.add_parser('info', help='Generate road info')
    info_parser.add_argument('input', help='Input CSV file path')



    args = parser.parse_args()

    if args.command == 'transform':
        input_gpx_file_path = args.input
        
        # Generate output paths if not provided
        if args.output_gpx:
            output_gpx_file_path = args.output_gpx
        else:
            base_name = os.path.splitext(input_gpx_file_path)[0]
            output_gpx_file_path = base_name + '-transformed.gpx'
            
        if args.output_csv:
            output_csv_file_path = args.output_csv
        else:
            base_name = os.path.splitext(input_gpx_file_path)[0]
            output_csv_file_path = base_name + '.csv'
        
        # Validate input file exists
        if not os.path.exists(input_gpx_file_path):
            print(f"Error: Input GPX file '{input_gpx_file_path}' does not exist.")
            sys.exit(1)
            
        print(f"Processing GPX file: {input_gpx_file_path}")
        print(f"Output GPX file: {output_gpx_file_path}")
        print(f"Output CSV file: {output_csv_file_path}")
        
        transform_route_info_from_gpx_file(
            input_gpx_file_path, 
            output_gpx_file_path, 
            output_csv_file_path,
            transform_coordinate=args.no_transform_coordinate,
            coordinate_type=args.coordinate_type,
            transformed_coordinate_type=args.transformed_coordinate_type,
            set_area=args.no_set_area,
            source=args.area_source,
            gdf_path=args.gdf_path,
            gdf_db_path=args.gdf_db_path
        )
        print("GPX processing completed successfully.")

    elif args.command == 'overlay':
        input_csv_file_path = args.input
        output_directory = args.output_dir
        start_index = args.start_index
        end_index = args.end_index
        start_index_after_fill = args.start_index_after_fill
        end_index_after_fill = args.end_index_after_fill
        crop_start = args.crop_start
        crop_end = args.crop_end
        
        # Validate input file exists
        if not os.path.exists(input_csv_file_path):
            print(f"Error: Input CSV file '{input_csv_file_path}' does not exist.")
            sys.exit(1)
            
        # Create output directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)
        
        print(f"Generating images from CSV: {input_csv_file_path}")
        print(f"Output directory: {output_directory}")
        
        generate_pic_from_csv(
            input_csv_file_path, out_dir=output_directory,
            start_index=start_index, end_index=end_index,
            start_index_after_fill=start_index_after_fill, end_index_after_fill=end_index_after_fill,
            crop_start=crop_start, crop_end=crop_end
        )
        print("Image generation completed successfully.")
    elif args.command == 'pad':
        code = args.code

        if args.output_svg:
            output_svg_file_path = args.output_svg
        else:
            output_svg_file_path = code + '.svg'

        print(f"Generating SVG num pad for code: {code}")
        print(f"Output SVG file: {output_svg_file_path}")
        # 第一位为大写字母，则为国道、省道等普通道路，或者是国家高速
        if code[0] in string.ascii_uppercase:
            if len(code) == 4:
                svg_drawing = generate_way_num_pad(code)
            else:
                svg_drawing = generate_expwy_pad(code, name=args.name)
        # 否则为省级高速，从第一位读省简称
        else:
            svg_drawing = generate_expwy_pad(code[1:], province=code[0], name=args.name)
        svg_drawing.saveas(output_svg_file_path)
        print("SVG num pad generation completed successfully.")
    elif args.command == 'info':
        input_csv_file_path = args.input
        if not os.path.exists(input_csv_file_path):
            print(f"Error: Input CSV file '{input_csv_file_path}' does not exist.")
            sys.exit(1)
        print(generate_road_info(input_csv_file_path))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()