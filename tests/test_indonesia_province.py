import pytest

from src.gpxutil.models.indonesia import INDONESIA_PROVINCE_CODE_MAP, get_indonesia_province_code

# 印尼 38 省（含 2022 年新设的巴布亚四省）→ ISO 3166-2:ID 两位代码。
# 键为 CSV 双字段：印尼语省名（province_id 字段）与中文省名（province 字段）。
EXPECTED_PROVINCE_CODES = {
    'Provinsi Aceh': '11', '亚齐特别行政区': '11',
    'Provinsi Sumatera Utara': '12', '北苏门答腊省': '12',
    'Provinsi Sumatera Barat': '13', '西苏门答腊省': '13',
    'Provinsi Riau': '14', '廖内省': '14',
    'Provinsi Jambi': '15', '占碑省': '15',
    'Provinsi Sumatera Selatan': '16', '南苏门答腊省': '16',
    'Provinsi Bengkulu': '17', '明古鲁省': '17',
    'Provinsi Lampung': '18', '楠榜省': '18',
    'Provinsi Kepulauan Bangka Belitung': '19', '邦加勿里洞群岛省': '19',
    'Provinsi Kepulauan Riau': '21', '廖内群岛省': '21',
    'Daerah Khusus Ibukota Jakarta': '31', '雅加达首都特区': '31',
    'Provinsi Jawa Barat': '32', '西爪哇省': '32',
    'Provinsi Jawa Tengah': '33', '中爪哇省': '33',
    'Daerah Istimewa Yogyakarta': '34', '日惹特区': '34',
    'Provinsi Jawa Timur': '35', '东爪哇省': '35',
    'Provinsi Banten': '36', '万丹省': '36',
    'Provinsi Bali': '51', '巴厘省': '51',
    'Provinsi Nusa Tenggara Barat': '52', '西努沙登加拉省': '52',
    'Provinsi Nusa Tenggara Timur': '53', '东努沙登加拉省': '53',
    'Provinsi Kalimantan Barat': '61', '西加里曼丹省': '61',
    'Provinsi Kalimantan Tengah': '62', '中加里曼丹省': '62',
    'Provinsi Kalimantan Selatan': '63', '南加里曼丹省': '63',
    'Provinsi Kalimantan Timur': '64', '东加里曼丹省': '64',
    'Provinsi Kalimantan Utara': '65', '北加里曼丹省': '65',
    'Provinsi Sulawesi Utara': '71', '北苏拉威西省': '71',
    'Provinsi Sulawesi Tengah': '72', '中苏拉威西省': '72',
    'Provinsi Sulawesi Selatan': '73', '南苏拉威西省': '73',
    'Provinsi Sulawesi Tenggara': '74', '东南苏拉威西省': '74',
    'Provinsi Gorontalo': '75', '哥伦打洛省': '75',
    'Provinsi Sulawesi Barat': '76', '西苏拉威西省': '76',
    'Provinsi Maluku': '81', '马鲁古省': '81',
    'Provinsi Maluku Utara': '82', '北马鲁古省': '82',
    'Provinsi Papua': '91', '巴布亚省': '91',
    'Provinsi Papua Barat': '92', '西巴布亚省': '92',
    'Provinsi Papua Selatan': '93', '南巴布亚省': '93',
    'Provinsi Papua Tengah': '94', '中巴布亚省': '94',
    'Provinsi Papua Pegunungan': '95', '高地巴布亚省': '95',
    'Provinsi Papua Barat Daya': '96', '西南巴布亚省': '96',
}


@pytest.mark.parametrize(
    ('province_name', 'expected_code'),
    [item for item in sorted(EXPECTED_PROVINCE_CODES.items())],
    ids=[k for k, _ in sorted(EXPECTED_PROVINCE_CODES.items())],
)
def test_province_code_map(province_name, expected_code):
    assert get_indonesia_province_code(province_name) == expected_code
    assert INDONESIA_PROVINCE_CODE_MAP[province_name] == expected_code


def test_map_complete():
    # 38 省 × 中/印尼语双键 = 76 条，无缺漏、无多余别名（锁住值错位）
    assert len(INDONESIA_PROVINCE_CODE_MAP) == len(EXPECTED_PROVINCE_CODES) == 76
    assert INDONESIA_PROVINCE_CODE_MAP == EXPECTED_PROVINCE_CODES


def test_province_code_unknown():
    assert get_indonesia_province_code('未知省份') is None
    assert get_indonesia_province_code(None) is None
