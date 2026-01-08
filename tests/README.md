# GPXUtil 测试说明

本项目包含对 main.py CLI 工具的全面测试，使用 pytest 框架。

## 测试文件结构

### [test_main_cli.py](./test_main_cli.py)
主要测试文件，包含以下测试用例：
- `test_transform_route_info_from_gpx_file_basic` - 测试基本 GPX 文件转换功能
- `test_transform_route_info_from_gpx_file_with_coordinates` - 测试带坐标转换的 GPX 处理
- `test_generate_road_info_with_mock_csv` - 测试路线信息生成功能
- `test_main_help` - 测试 CLI 帮助信息
- `test_main_transform_command_with_mock` - 测试 transform 子命令
- `test_main_pad_command_with_mock` - 测试 pad 子命令
- `test_main_overlay_command_with_mock` - 测试 overlay 子命令
- `test_main_info_command_with_mock` - 测试 info 子命令
- `test_invalid_input_file_error` - 测试输入文件不存在的错误处理
- `test_generate_way_num_pad_and_expwy_pad_functions` - 测试 SVG 生成函数

### [test_cli_arguments.py](./test_cli_arguments.py)
CLI 参数解析和验证测试，包含以下测试用例：
- `test_cli_transform_command_with_all_parameters` - 测试 transform 命令的所有参数
- `test_cli_transform_command_no_transform` - 测试禁用坐标转换的情况
- `test_cli_area_source_validation` - 测试区域信息源参数验证
- `test_cli_output_paths_generation` - 测试输出路径自动生成
- `test_cli_invalid_area_source_fails` - 测试无效参数的错误处理

## 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_main_cli.py -v

# 运行特定测试函数
python -m pytest tests/test_main_cli.py::test_transform_route_info_from_gpx_file_basic -v
```

## 测试覆盖范围

- CLI 子命令：transform, pad, overlay, info
- 参数验证：area_source, coordinate_type, transformed_coordinate_type, 等
- 文件处理：GPX, CSV, SVG
- 错误处理：文件不存在、无效参数
- 功能验证：坐标转换、区域信息获取、道路标识生成