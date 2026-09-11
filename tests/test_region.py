from src.gpxutil.models.region import Region, get_default_languages, get_field_suffix, get_field_value


def test_region_values():
    assert Region.CN.value == 'cn'
    assert Region.ID.value == 'id'


def test_default_languages_cn():
    assert get_default_languages(Region.CN) == ('zh', ['en'])


def test_default_languages_id():
    assert get_default_languages(Region.ID) == ('zh', ['id', 'en'])


def test_field_suffix():
    assert get_field_suffix('zh') == ''
    assert get_field_suffix('id') == '_id'
    assert get_field_suffix('en') == '_en'


def test_get_field_value_zh_prefers_plain_column():
    """主语言 zh：无后缀列有值时优先使用，不被 _zh 列覆盖"""
    row = {'province': '河南省', 'province_zh': '河南'}
    assert get_field_value(row, 'province', 'zh') == '河南省'


def test_get_field_value_zh_falls_back_to_zh_suffix():
    """主语言 zh：无后缀列缺失或为空时回退 _zh 后缀列"""
    assert get_field_value({'province_zh': '河南省'}, 'province', 'zh') == '河南省'
    assert get_field_value({'province': '', 'province_zh': '河南省'}, 'province', 'zh') == '河南省'


def test_get_field_value_secondary_language():
    """副语言按标准后缀取列，列缺失或值为空返回空串"""
    assert get_field_value({'province_en': 'Henan Province'}, 'province', 'en') == 'Henan Province'
    assert get_field_value({}, 'province', 'en') == ''
    assert get_field_value({'province_id': None}, 'province', 'id') == ''
