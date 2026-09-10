import pytest

from src.gpxutil.models.indonesia import INDONESIA_PROVINCE_CODE_MAP, get_indonesia_province_code

# 印尼 34 省（2019 年）→ 道路编号的地区代码（kode wilayah，Peraturan Dirjen Hubdat
# KP.1324/AJ.001/DRJD/2019 Lampiran I）。与行政区划代码（BPS）无关：
# 如中爪哇的 kode wilayah 为 14，而 BPS 代码为 33。
# 键为 CSV 三字段：印尼语省名（province_id 字段）、中文省名（province 字段）
# 与英文省名（province_en 字段）。
EXPECTED_PROVINCE_CODES = {
    'Provinsi Aceh': '1', '亚齐特别行政区': '1', 'Province of Aceh': '1',
    'Provinsi Sumatera Utara': '2', '北苏门答腊省': '2', 'Province of North Sumatra': '2',
    'Provinsi Riau': '3', '廖内省': '3', 'Province of Riau': '3',
    'Provinsi Sumatera Barat': '4', '西苏门答腊省': '4', 'Province of West Sumatra': '4',
    'Provinsi Jambi': '5', '占碑省': '5', 'Province of Jambi': '5',
    'Provinsi Sumatera Selatan': '6', '南苏门答腊省': '6', 'Province of South Sumatra': '6',
    'Provinsi Bengkulu': '7', '明古鲁省': '7', 'Province of Bengkulu': '7',
    'Provinsi Lampung': '8', '楠榜省': '8', 'Province of Lampung': '8',
    'Provinsi Kepulauan Riau': '9', '廖内群岛省': '9', 'Province of Riau Islands': '9',
    'Provinsi Kepulauan Bangka Belitung': '10', '邦加勿里洞群岛省': '10', 'Province of Bangka Belitung Islands': '10',
    'Provinsi Banten': '11', '万丹省': '11', 'Province of Banten': '11',
    'Provinsi Jawa Barat': '12', '西爪哇省': '12', 'Province of West Java': '12',
    'Daerah Khusus Ibukota Jakarta': '13', '雅加达首都特区': '13', 'Special Capital Region of Jakarta': '13',
    'Provinsi Jawa Tengah': '14', '中爪哇省': '14', 'Province of Central Java': '14',
    'Daerah Istimewa Yogyakarta': '15', '日惹特区': '15', 'Special Region of Yogyakarta': '15',
    'Provinsi Jawa Timur': '16', '东爪哇省': '16', 'Province of East Java': '16',
    'Provinsi Bali': '17', '巴厘省': '17', 'Province of Bali': '17',
    'Provinsi Nusa Tenggara Barat': '18', '西努沙登加拉省': '18', 'Province of West Nusa Tenggara': '18',
    'Provinsi Nusa Tenggara Timur': '19', '东努沙登加拉省': '19', 'Province of East Nusa Tenggara': '19',
    'Provinsi Kalimantan Barat': '20', '西加里曼丹省': '20', 'Province of West Kalimantan': '20',
    'Provinsi Kalimantan Tengah': '21', '中加里曼丹省': '21', 'Province of Central Kalimantan': '21',
    'Provinsi Kalimantan Selatan': '22', '南加里曼丹省': '22', 'Province of South Kalimantan': '22',
    'Provinsi Kalimantan Timur': '23', '东加里曼丹省': '23', 'Province of East Kalimantan': '23',
    'Provinsi Kalimantan Utara': '24', '北加里曼丹省': '24', 'Province of North Kalimantan': '24',
    'Provinsi Sulawesi Selatan': '25', '南苏拉威西省': '25', 'Province of South Sulawesi': '25',
    'Provinsi Sulawesi Barat': '26', '西苏拉威西省': '26', 'Province of West Sulawesi': '26',
    'Provinsi Sulawesi Tenggara': '27', '东南苏拉威西省': '27', 'Province of Southeast Sulawesi': '27',
    'Provinsi Sulawesi Tengah': '28', '中苏拉威西省': '28', 'Province of Central Sulawesi': '28',
    'Provinsi Gorontalo': '29', '哥伦打洛省': '29', 'Province of Gorontalo': '29',
    'Provinsi Sulawesi Utara': '30', '北苏拉威西省': '30', 'Province of North Sulawesi': '30',
    'Provinsi Maluku': '31', '马鲁古省': '31', 'Province of Maluku': '31',
    'Provinsi Maluku Utara': '32', '北马鲁古省': '32', 'Province of North Maluku': '32',
    'Provinsi Papua Barat': '33', '西巴布亚省': '33', 'Province of West Papua': '33',
    'Provinsi Papua': '34', '巴布亚省': '34', 'Province of Papua': '34',
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
    # 34 省 × 三语键 = 102 条，无缺漏、无多余别名（锁住值错位）
    assert len(INDONESIA_PROVINCE_CODE_MAP) == len(EXPECTED_PROVINCE_CODES) == 102
    assert INDONESIA_PROVINCE_CODE_MAP == EXPECTED_PROVINCE_CODES


def test_province_code_unknown():
    assert get_indonesia_province_code('未知省份') is None
    assert get_indonesia_province_code(None) is None
