"""start_index / end_index 应按下 CSV 的 index 列值过滤（而非行位置切片），且默认 -1 不丢最后一行"""
import src.gpxutil.utils.create_pic as create_pic
from src.gpxutil.models.region import Region


def make_row(index: int, et: int) -> dict:
    """构造与 read_csv 输出结构一致的行"""
    return {
        'index': str(index), 'elapsed_time': et,
        'distance': float(et), 'speed': None, 'course': None, 'elevation': None,
    }


def read_with(rows, monkeypatch, **kwargs):
    monkeypatch.setattr(create_pic, 'read_csv', lambda path: rows)
    monkeypatch.setattr(create_pic, 'build_area_texts', lambda row, region: [])
    monkeypatch.setattr(create_pic, 'build_road_texts', lambda row, region: [])
    monkeypatch.setattr(create_pic, 'parse_road_signs', lambda row, region: [])
    return create_pic.read_csv_with_additional_info('dummy.csv', region=Region.CN, **kwargs)


# 不关心 crop 行为的测试统一显式传大 crop_end，避免 crop 干扰
NO_CROP = dict(crop_end=10 ** 9)


def test_end_index_filters_by_index_column(monkeypatch):
    """index 列有跳变时，end_index 按 index 列值过滤，而不是按行位置切片"""
    # 行位置 0,1,2 对应的 index 为 0,5,6；用户期望 end_index=2 时只取 index<=2 的行
    rows = [make_row(0, 0), make_row(5, 50), make_row(6, 51)]
    result = read_with(rows, monkeypatch, end_index=2, **NO_CROP)
    # 仅 index 0 一行，fill 后 elapsed_time 0..0 共 1 帧
    assert len(result) == 1
    assert result[0]['index'] == '0'


def test_end_index_includes_boundary_row(monkeypatch):
    """end_index 为闭区间：包含 index 列值等于 end_index 的行"""
    rows = [make_row(0, 0), make_row(1, 1), make_row(2, 2)]
    result = read_with(rows, monkeypatch, end_index=1, **NO_CROP)
    # index 0..1 两行，fill 后 elapsed_time 0..1 共 2 帧
    assert len(result) == 2
    assert result[0]['index'] == '0'
    assert result[1]['index'] == '1'


def test_default_end_keeps_last_row(monkeypatch):
    """end_index 与 end_index_after_fill 默认 -1 时不得丢掉最后一行"""
    rows = [make_row(0, 0), make_row(1, 1)]
    result = read_with(rows, monkeypatch, **NO_CROP)
    assert len(result) == 2
    assert result[-1]['index'] == '1'


def test_start_index_filters_by_index_column(monkeypatch):
    """start_index 按 index 列值过滤"""
    rows = [make_row(0, 0), make_row(2, 2), make_row(3, 3)]
    result = read_with(rows, monkeypatch, start_index=2, **NO_CROP)
    assert len(result) == 2
    assert result[0]['index'] == '2'


def test_crop_end_default_does_not_clip(monkeypatch):
    """crop_end 默认 -1 表示不裁剪；index 列跳变时旧的 len 近似会把尾部行误裁掉"""
    rows = [make_row(0, 0), make_row(10, 1)]
    result = read_with(rows, monkeypatch)
    assert len(result) == 2
    assert result[-1]['index'] == '10'


def test_crop_end_explicit_filters_by_index_column(monkeypatch):
    """显式 crop_end 按 index 列值过滤（闭区间），行为与修复前一致"""
    # et 连续以避免 fill 补帧行干扰 crop 判定
    rows = [make_row(0, 0), make_row(5, 1), make_row(6, 2)]
    result = read_with(rows, monkeypatch, crop_end=5)
    assert len(result) == 2
    assert result[-1]['index'] == '5'
