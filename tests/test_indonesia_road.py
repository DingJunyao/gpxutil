from src.gpxutil.models.indonesia import IndonesiaRoadLevel, IndonesiaRoadInfo, parse_indonesia_road_num
from src.gpxutil.models.road import IndonesiaRoad

TOL_KEYWORDS = ['收费', 'Tol']
PROVINCES = ['Provinsi Jawa Timur', '东爪哇省']


def test_nasional():
    info = parse_indonesia_road_num('3', 'Jl. Nasional III', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.NASIONAL
    assert info.code == '3'
    assert info.province_code == '35'


def test_tol_by_chinese_keyword():
    info = parse_indonesia_road_num('8', '泗水-波龙收费公路', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.TOL
    assert info.code == '8'


def test_tol_by_indonesian_keyword():
    info = parse_indonesia_road_num('8', 'Jl. Tol Pandaan - Malang', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.TOL


def test_provinsi_three_digit():
    info = parse_indonesia_road_num('023', '图姆庞大街', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.PROVINSI
    assert info.code == '023'
    assert info.province_code == '35'


def test_provinsi_with_embedded_province():
    info = parse_indonesia_road_num('35-024', '图卢斯阿尤大街', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.PROVINSI
    assert info.code == '024'
    assert info.province_code == '35'


def test_provinsi_embedded_prefix_not_in_code_map_falls_back():
    # 'abc-023'：前缀非省码，不得作为省码返回，回退到 province_texts 查找
    info = parse_indonesia_road_num('abc-023', '某路', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.PROVINSI
    assert info.code == '023'
    assert info.province_code == '35'


def test_provinsi_embedded_prefix_unused_code_falls_back():
    # '99-024'：'99' 不在省份代码表中，回退到 province_texts 查找
    info = parse_indonesia_road_num('99-024', '某路', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.PROVINSI
    assert info.code == '024'
    assert info.province_code == '35'


def test_provinsi_empty_embedded_prefix_falls_back():
    # '-024'：空前缀不得产生空串省码，回退到 province_texts 查找
    info = parse_indonesia_road_num('-024', '某路', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.PROVINSI
    assert info.code == '024'
    assert info.province_code == '35'


def test_provinsi_with_spaces_around_hyphen():
    # 连字符两侧空白：各段 strip 后再解析
    info = parse_indonesia_road_num(' 35 - 024 ', '图卢斯阿尤大街', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.PROVINSI
    assert info.code == '024'
    assert info.province_code == '35'


def test_road_num_unicode_digit_not_recognized():
    # 全角数字等 Unicode 数字不算有效编号
    assert parse_indonesia_road_num('３', '某路', PROVINCES, TOL_KEYWORDS) is None
    assert parse_indonesia_road_num('35-０２４', '某路', PROVINCES, TOL_KEYWORDS) is None


def test_provinsi_no_province_anywhere():
    info = parse_indonesia_road_num('023', '某路', [], TOL_KEYWORDS)
    assert info.province_code is None


def test_empty_road_num():
    assert parse_indonesia_road_num('', '某路', PROVINCES, TOL_KEYWORDS) is None
    assert parse_indonesia_road_num(None, '某路', PROVINCES, TOL_KEYWORDS) is None


def test_indonesia_road_class():
    road = IndonesiaRoad('023', '图姆庞大街', ['Provinsi Jawa Timur'])
    assert road.have_sign is True
    assert road.level == IndonesiaRoadLevel.PROVINSI
    assert road.code == '023'
    assert road.province_code == '35'
    assert road.to_svg() is not None


def test_indonesia_road_no_sign():
    road = IndonesiaRoad('', '某路', [])
    assert road.have_sign is False
