from src.gpxutil.models.region import Region, get_default_languages, get_field_suffix


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
