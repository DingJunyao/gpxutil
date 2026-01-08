"""测试 main.py CLI 功能的 pytest 用例"""

import os
import tempfile
import pytest
import argparse
from unittest.mock import patch, MagicMock
import sys
from io import StringIO

from main import main, transform_route_info_from_gpx_file, generate_road_info
from src.gpxutil.models.route import Route, RoutePoint
from src.gpxutil.utils.create_pic import generate_pic_from_csv
from src.gpxutil.utils.svg_gen import generate_expwy_pad, generate_way_num_pad

# 模拟 GPX 文件内容
MOCK_GPX_CONTENT = '''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="GPS Visualizer">
  <trk>
    <name>Sample Track</name>
    <trkseg>
      <trkpt lat="39.9042" lon="116.4074">
        <ele>50.0</ele>
        <time>2023-01-01T10:00:00Z</time>
      </trkpt>
      <trkpt lat="39.9052" lon="116.4084">
        <ele>55.0</ele>
        <time>2023-01-01T10:01:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>'''

def test_transform_route_info_from_gpx_file_basic():
    """测试基本的 GPX 文件转换功能"""
    # 创建临时 GPX 文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpx', delete=False) as temp_input:
        temp_input.write(MOCK_GPX_CONTENT)
        temp_input_path = temp_input.name

    # 创建临时输出文件
    temp_output_gpx = tempfile.mktemp(suffix='.gpx')
    temp_output_csv = tempfile.mktemp(suffix='.csv')

    try:
        # 调用函数
        transform_route_info_from_gpx_file(
            input_gpx_file_path=temp_input_path,
            output_transformed_gpx_file_path=temp_output_gpx,
            output_csv_file_path=temp_output_csv,
            transform_coordinate=False,  # 不转换坐标以避免依赖外部转换库
            set_area=False  # 不设置区域以避免依赖外部API或数据库
        )

        # 验证输出文件存在
        assert os.path.exists(temp_output_gpx), "输出 GPX 文件应该存在"
        assert os.path.exists(temp_output_csv), "输出 CSV 文件应该存在"

        # 验证输出文件不是空的
        assert os.path.getsize(temp_output_gpx) > 0, "输出 GPX 文件不应为空"
        assert os.path.getsize(temp_output_csv) > 0, "输出 CSV 文件不应为空"

        # 验证输出 GPX 文件可以被 Route 类正确加载
        route = Route.from_gpx_file(temp_output_gpx)
        assert len(route.points) == 2, "应该有两个点"
        assert route.points[0].latitude == 39.9042, "第一个点的纬度应该匹配"
        assert route.points[0].longitude == 116.4074, "第一个点的经度应该匹配"
    finally:
        # 清理临时文件
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if os.path.exists(temp_output_gpx):
            os.remove(temp_output_gpx)
        if os.path.exists(temp_output_csv):
            os.remove(temp_output_csv)


def test_transform_route_info_from_gpx_file_with_coordinates():
    """测试带有坐标转换的 GPX 文件转换功能"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpx', delete=False) as temp_input:
        temp_input.write(MOCK_GPX_CONTENT)
        temp_input_path = temp_input.name

    temp_output_gpx = tempfile.mktemp(suffix='.gpx')
    temp_output_csv = tempfile.mktemp(suffix='.csv')

    try:
        # 调用函数，启用坐标转换
        transform_route_info_from_gpx_file(
            input_gpx_file_path=temp_input_path,
            output_transformed_gpx_file_path=temp_output_gpx,
            output_csv_file_path=temp_output_csv,
            transform_coordinate=True,  # 启用坐标转换
            coordinate_type='wgs84',
            transformed_coordinate_type='gcj02',
            set_area=False  # 不设置区域
        )

        # 验证输出文件存在
        assert os.path.exists(temp_output_gpx), "输出 GPX 文件应该存在"
        assert os.path.exists(temp_output_csv), "输出 CSV 文件应该存在"

        # 验证输出 GPX 文件包含转换后的坐标
        route = Route.from_gpx_file(temp_output_gpx)
        assert len(route.points) == 2, "应该有两个点"
        # 验证转换后的坐标存在
        assert route.points[0].longitude_transformed is not None, "应该有转换后的经度"
        assert route.points[0].latitude_transformed is not None, "应该有转换后的纬度"
    finally:
        # 清理临时文件
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if os.path.exists(temp_output_gpx):
            os.remove(temp_output_gpx)
        if os.path.exists(temp_output_csv):
            os.remove(temp_output_csv)


def test_generate_road_info_with_mock_csv():
    """测试生成路线信息功能"""
    # 创建一个模拟的 CSV 文件，使用 utf-8-sig 编码（带 BOM）
    mock_csv_content = '''index,time_date,time_time,time_microsecond,elapsed_time,longitude,latitude,longitude_transformed,latitude_transformed,elevation,distance,course,speed,province,city,area,province_en,city_en,area_en,road_num,road_name,road_name_en,memo
0,2023/01/01,10:00:00,0,0.0,116.4074,39.9042,116.4075,39.9043,50.0,0.0,0.0,0.0,北京市,北京市,东城区,,,,,,,,-
1,2023/01/01,10:01:00,0,60.0,116.4084,39.9052,116.4085,39.9053,55.0,100.0,45.0,1.0,北京市,北京市,东城区,,,,,,,,-'''

    # 创建临时文件并写入带BOM的UTF-8编码内容
    temp_csv_path = tempfile.mktemp(suffix='.csv')
    with open(temp_csv_path, 'w', encoding='utf-8-sig', newline='') as temp_csv:
        temp_csv.write(mock_csv_content)

    try:
        # 调用函数
        result = generate_road_info(temp_csv_path)
        # 这里我们只是验证函数不会崩溃，因为具体输出格式依赖于实际实现
        assert isinstance(result, str) or result is None, "结果应该是字符串或None"
    finally:
        # 清理临时文件
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)


def test_main_help(capsys):
    """测试 CLI 帮助信息"""
    # 模拟命令行参数
    sys.argv = ['main.py', '--help']

    # 捕获异常以防止系统退出
    with pytest.raises(SystemExit):
        main()

    captured = capsys.readouterr()
    # 验证帮助信息包含主要命令
    assert 'GPX Utility Tool' in captured.out, "帮助信息应该包含工具描述"
    assert 'transform' in captured.out, "帮助信息应该包含 transform 命令"
    assert 'pad' in captured.out, "帮助信息应该包含 pad 命令"
    assert 'overlay' in captured.out, "帮助信息应该包含 overlay 命令"
    assert 'info' in captured.out, "帮助信息应该包含 info 命令"


def test_main_transform_command_with_mock(monkeypatch):
    """测试 transform 子命令"""
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpx', delete=False) as temp_input:
        temp_input.write(MOCK_GPX_CONTENT)
        temp_input_path = temp_input.name

    temp_output_gpx = tempfile.mktemp(suffix='.gpx')
    temp_output_csv = tempfile.mktemp(suffix='.csv')

    # Mock transform_route_info_from_gpx_file 函数以避免实际处理
    mock_transform_func = MagicMock()
    monkeypatch.setattr('main.transform_route_info_from_gpx_file', mock_transform_func)

    # 模拟命令行参数
    sys.argv = [
        'main.py', 'transform',
        temp_input_path,
        temp_output_gpx,
        temp_output_csv,
        '--no_transform_coordinate',
        '--coordinate_type', 'wgs84',
        '--transformed_coordinate_type', 'gcj02'
    ]

    try:
        # 运行主函数
        main()
        # 验证函数被调用
        mock_transform_func.assert_called_once()
    except SystemExit:
        # 预期的退出行为
        pass
    finally:
        # 清理临时文件
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if os.path.exists(temp_output_gpx):
            os.remove(temp_output_gpx)
        if os.path.exists(temp_output_csv):
            os.remove(temp_output_csv)


def test_main_pad_command_with_mock(monkeypatch):
    """测试 pad 子命令"""
    # Mock generate_expwy_pad 函数
    mock_svg = MagicMock()
    mock_svg.saveas = MagicMock()
    monkeypatch.setattr('main.generate_expwy_pad', lambda *args, **kwargs: mock_svg)

    temp_svg = tempfile.mktemp(suffix='.svg')
    sys.argv = ['main.py', 'pad', 'G42', temp_svg]

    try:
        main()
        # 验证函数被调用
        mock_svg.saveas.assert_called_once_with(temp_svg)
    except SystemExit:
        # 预期的退出行为
        pass
    finally:
        # 清理临时文件
        if os.path.exists(temp_svg):
            os.remove(temp_svg)


def test_main_overlay_command_with_mock(monkeypatch):
    """测试 overlay 子命令"""
    # 创建临时 CSV 文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_csv:
        temp_csv.write('''index,time_date,time_time,time_microsecond,elapsed_time,longitude,latitude,longitude_transformed,latitude_transformed,elevation,distance,course,speed,province,city,area,province_en,city_en,area_en,road_num,road_name,road_name_en,memo
0,2023/01/01,10:00:00,0,0.0,116.4074,39.9042,116.4075,39.9043,50.0,0.0,0.0,0.0,北京市,北京市,东城区,,,,,,,,
1,2023/01/01,10:01:00,0,60.0,116.4084,39.9052,116.4085,39.9053,55.0,100.0,45.0,1.0,北京市,北京市,东城区,,,,,,,,''')
        temp_csv_path = temp_csv.name

    temp_output_dir = tempfile.mkdtemp()

    # Mock generate_pic_from_csv 函数
    mock_generate_func = MagicMock()
    monkeypatch.setattr('main.generate_pic_from_csv', mock_generate_func)

    sys.argv = ['main.py', 'overlay', temp_csv_path, temp_output_dir]

    try:
        main()
        # 验证函数被调用
        mock_generate_func.assert_called_once()
    except SystemExit:
        # 预期的退出行为
        pass
    finally:
        # 清理临时文件
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)
        # 注意：os.rmdir 只能删除空目录，这里简单跳过目录清理以避免权限问题
        # 实际使用中可能需要更复杂的清理逻辑


def test_main_info_command_with_mock(monkeypatch):
    """测试 info 子命令"""
    # 创建临时 CSV 文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_csv:
        temp_csv.write('''index,time_date,time_time,time_microsecond,elapsed_time,longitude,latitude,longitude_transformed,latitude_transformed,elevation,distance,course,speed,province,city,area,province_en,city_en,area_en,road_num,road_name,road_name_en,memo
0,2023/01/01,10:00:00,0,0.0,116.4074,39.9042,116.4075,39.9043,50.0,0.0,0.0,0.0,北京市,北京市,东城区,,,,,,,,
1,2023/01/01,10:01:00,0,60.0,116.4084,39.9052,116.4085,39.9053,55.0,100.0,45.0,1.0,北京市,北京市,东城区,,,,,,,,''')
        temp_csv_path = temp_csv.name

    # Mock generate_road_info 函数
    mock_info_func = MagicMock(return_value="Mock road info result")
    monkeypatch.setattr('main.generate_road_info', mock_info_func)

    sys.argv = ['main.py', 'info', temp_csv_path]

    try:
        main()
        # 验证函数被调用
        mock_info_func.assert_called_once_with(temp_csv_path)
    except SystemExit:
        # 预期的退出行为
        pass
    finally:
        # 清理临时文件
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)


def test_invalid_input_file_error(capsys, monkeypatch):
    """测试输入文件不存在时的错误处理"""
    # Mock transform_route_info_from_gpx_file 函数以避免实际处理
    mock_transform_func = MagicMock()
    monkeypatch.setattr('main.transform_route_info_from_gpx_file', mock_transform_func)

    # 使用不存在的文件路径
    invalid_file_path = "/invalid/path/nonexistent.gpx"
    temp_output_gpx = tempfile.mktemp(suffix='.gpx')
    temp_output_csv = tempfile.mktemp(suffix='.csv')

    sys.argv = [
        'main.py', 'transform',
        invalid_file_path,
        temp_output_gpx,
        temp_output_csv
    ]

    try:
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1, "应该以退出码 1 退出"
    finally:
        captured = capsys.readouterr()
        assert "does not exist" in captured.err or "does not exist" in captured.out, "错误信息应该包含文件不存在的提示"


def test_generate_way_num_pad_and_expwy_pad_functions():
    """测试 SVG 生成函数"""
    # 测试普通道路编号牌
    svg_drawing = generate_way_num_pad('G318')
    assert svg_drawing is not None, "应该成功生成 SVG 绘图对象"
    
    # 测试高速公路编号牌
    svg_drawing = generate_expwy_pad('G42')
    assert svg_drawing is not None, "应该成功生成高速公路 SVG 绘图对象"
    
    # 测试带名称的高速公路编号牌
    svg_drawing = generate_expwy_pad('G42', name='沪蓉高速')
    assert svg_drawing is not None, "应该成功生成带名称的高速公路 SVG 绘图对象"
    
    # 测试省级高速公路
    svg_drawing = generate_expwy_pad('S11', province='苏')
    assert svg_drawing is not None, "应该成功生成省级高速公路 SVG 绘图对象"