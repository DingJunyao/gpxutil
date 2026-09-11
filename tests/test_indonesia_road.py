from src.gpxutil.models.indonesia import IndonesiaRoadLevel, IndonesiaRoadInfo, parse_indonesia_road_num
from src.gpxutil.models.road import IndonesiaRoad

TOL_KEYWORDS = ['收费', 'Tol']
# 东爪哇省的 kode wilayah（KP.1324/AJ.001/DRJD/2019 Lampiran I）为 16
PROVINCES = ['Provinsi Jawa Timur', '东爪哇省']


def test_nasional():
    info = parse_indonesia_road_num('3', 'Jl. Nasional III', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.NASIONAL
    assert info.code == '3'
    assert info.region_code == '16'


def test_tol_by_chinese_keyword():
    info = parse_indonesia_road_num('8', '泗水-波龙收费公路', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.TOL
    assert info.code == '8'


def test_tol_by_indonesian_keyword():
    info = parse_indonesia_road_num('8', 'Jl. Tol Pandaan - Malang', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.TOL


def test_tol_by_secondary_language_name():
    # 主语言路名不含关键词、印尼语路名含 'Tol'：多语言候选路名任一命中即判 TOL
    info = parse_indonesia_road_num('1', ['图卢斯阿尤大街', 'Jalan Tol Tulus Ayu'], PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.TOL


def test_nasional_when_no_candidate_name_matches():
    # 候选路名全不含关键词：仍判 NASIONAL
    info = parse_indonesia_road_num('1', ['图卢斯阿尤大街', 'Tulus Ayu Main Rd.'], PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.NASIONAL


def test_road_name_candidates_accept_none_members():
    # 候选列表允许 None/空串成员（缺副语言列的行）
    info = parse_indonesia_road_num('1', ['图卢斯阿尤大街', None, ''], PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.NASIONAL


def test_force_tol_without_name():
    # 无路名时用 force_tol 强制判定为收费公路
    info = parse_indonesia_road_num('8', None, PROVINCES, TOL_KEYWORDS, force_tol=True)
    assert info.level == IndonesiaRoadLevel.TOL
    assert info.code == '8'


def test_force_tol_ignored_for_three_digit():
    # force_tol 对 3 位编号（省道）无效
    info = parse_indonesia_road_num('023', None, PROVINCES, TOL_KEYWORDS, force_tol=True)
    assert info.level == IndonesiaRoadLevel.PROVINSI


def test_province_texts_accept_region_code():
    # province_texts 直接传省级地区代码（如 '16'）也有效
    info = parse_indonesia_road_num('024', '某路', ['16'], TOL_KEYWORDS)
    assert info.region_code == '16'


def test_province_texts_accept_english_name():
    info = parse_indonesia_road_num('024', '某路', ['Province of East Java'], TOL_KEYWORDS)
    assert info.region_code == '16'


def test_provinsi_three_digit():
    info = parse_indonesia_road_num('023', '图姆庞大街', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.PROVINSI
    assert info.code == '023'
    assert info.region_code == '16'


def test_provinsi_with_embedded_province():
    info = parse_indonesia_road_num('16-024', '图卢斯阿尤大街', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.PROVINSI
    assert info.code == '024'
    assert info.region_code == '16'


def test_provinsi_with_embedded_city_code():
    # 县市码内嵌（'16.17' = 东爪哇第 17 个县/市）：色带显示 'PROVINSI 16.17'
    info = parse_indonesia_road_num('16.17-024', '图卢斯阿尤大街', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.PROVINSI
    assert info.code == '024'
    assert info.region_code == '16.17'


def test_provinsi_embedded_prefix_not_in_code_map_falls_back():
    # 'abc-023'：前缀非省码，不得作为地区代码，回退到 province_texts 查找
    info = parse_indonesia_road_num('abc-023', '某路', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.PROVINSI
    assert info.code == '023'
    assert info.region_code == '16'


def test_provinsi_embedded_prefix_unused_code_falls_back():
    # '99-024'：'99' 不在省份代码表中，回退到 province_texts 查找
    info = parse_indonesia_road_num('99-024', '某路', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.PROVINSI
    assert info.code == '024'
    assert info.region_code == '16'


def test_provinsi_empty_embedded_prefix_falls_back():
    # '-024'：空前缀不得产生空串地区代码，回退到 province_texts 查找
    info = parse_indonesia_road_num('-024', '某路', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.PROVINSI
    assert info.code == '024'
    assert info.region_code == '16'


def test_provinsi_with_spaces_around_hyphen():
    # 连字符两侧空白：各段 strip 后再解析
    info = parse_indonesia_road_num(' 16 - 024 ', '图卢斯阿尤大街', PROVINCES, TOL_KEYWORDS)
    assert info.level == IndonesiaRoadLevel.PROVINSI
    assert info.code == '024'
    assert info.region_code == '16'


def test_road_num_unicode_digit_not_recognized():
    # 全角数字等 Unicode 数字不算有效编号
    assert parse_indonesia_road_num('３', '某路', PROVINCES, TOL_KEYWORDS) is None
    assert parse_indonesia_road_num('16-０２４', '某路', PROVINCES, TOL_KEYWORDS) is None


def test_provinsi_no_province_anywhere():
    info = parse_indonesia_road_num('023', '某路', [], TOL_KEYWORDS)
    assert info.region_code is None


def test_empty_road_num():
    assert parse_indonesia_road_num('', '某路', PROVINCES, TOL_KEYWORDS) is None
    assert parse_indonesia_road_num(None, '某路', PROVINCES, TOL_KEYWORDS) is None


def test_indonesia_road_class():
    road = IndonesiaRoad('023', '图姆庞大街', ['Provinsi Jawa Timur'])
    assert road.have_sign is True
    assert road.level == IndonesiaRoadLevel.PROVINSI
    assert road.code == '023'
    assert road.region_code == '16'
    assert road.to_svg() is not None


def test_indonesia_road_class_multi_lang_names():
    # 类接口同样接受候选路名列表：主语言名作展示名，印尼语名命中 TOL
    road = IndonesiaRoad('1', ['图卢斯阿尤大街', 'Jalan Tol Tulus Ayu'], ['Provinsi Jawa Timur'])
    assert road.level == IndonesiaRoadLevel.TOL
    assert road.name == '图卢斯阿尤大街'


def test_indonesia_road_no_sign():
    road = IndonesiaRoad('', '某路', [])
    assert road.have_sign is False
