"""印尼道路与行政区划相关数据与逻辑"""
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, unique

# 印尼道路编号的地区代码（kode wilayah，Peraturan Dirjen Hubdat
# KP.1324/AJ.001/DRJD/2019 Lampiran I）：省级为 1-34 序号，与行政区划代码（BPS）无关；
# 县市级为"省码.省内序号"（如 '14.17' 即中爪哇 Rembang 县）。
# 键为 CSV 三字段：印尼语省名（province_id 字段）、中文省名（province 字段）
# 与英文省名（province_en 字段）。
# 注：2022 年新设的巴布亚四省尚无法规代码，未收录。
INDONESIA_PROVINCE_CODE_MAP = {
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


def get_indonesia_province_code(province_text: str | None) -> str | None:
    """按印尼语省名或中文省名查省份代码，查不到返回 None"""
    if not province_text:
        return None
    return INDONESIA_PROVINCE_CODE_MAP.get(province_text)


@unique
class IndonesiaRoadLevel(Enum):
    NASIONAL = 1
    TOL = 2
    PROVINSI = 3


@dataclass
class IndonesiaRoadInfo:
    """解析后的印尼道路信息"""
    level: IndonesiaRoadLevel
    code: str              # 纯编号，盾牌大字显示用（如 '024'）
    region_code: str | None  # 地区代码，色带显示用（NASIONAL/TOL 为省码如 '16'，
                             # PROVINSI 为县市码如 '16.17'）


def parse_indonesia_road_num(
        road_num: str | None, road_names: str | Sequence[str | None] | None,
        province_texts: Sequence[str | None], tol_keywords: list[str],
        force_tol: bool = False
) -> IndonesiaRoadInfo | None:
    """
    解析印尼道路编号。
    :param road_num: CSV road_num 字段，如 '3'、'023'、'16-024'、'16.17-024'；空则无盾牌
    :param road_names: 候选路名（各语言路名列），任一含 tol_keywords 关键词即判 TOL；
                       允许单个字符串、None 或含 None/空串成员的序列
    :param province_texts: 候选省份（印尼语/中文/英文省名，或省级地区代码），按顺序查省码
    :param tol_keywords: TOL 判定关键词（如 ['收费', 'Tol']）
    :param force_tol: 强制按收费公路（TOL）解析，仅 1-2 位编号有效
    :return: 解析结果；无法识别返回 None
    """
    if not road_num:
        return None
    road_num = road_num.strip()

    region_code = None
    if '-' in road_num:
        # 连字符前为地区代码：'16-024'（省码）、'16.17-024'（县市码）；
        # 须命中省份代码表（或为省码.县序号形式）才作为地区代码，
        # 否则（含 'abc-024'、'99-024'、'-024' 等）回退到下方 province_texts 查找
        embedded, code = road_num.split('-', 1)
        embedded, code = embedded.strip(), code.strip()
        if embedded in INDONESIA_PROVINCE_CODE_MAP.values():
            region_code = embedded
        elif '.' in embedded:
            province_part, city_part = embedded.split('.', 1)
            if (province_part in INDONESIA_PROVINCE_CODE_MAP.values()
                    and city_part.isascii() and city_part.isdigit()):
                region_code = embedded
    else:
        code = road_num.strip()

    # 仅接受 ASCII 数字，'３'（全角）等 Unicode 数字视为无法识别
    if not (code.isascii() and code.isdigit()):
        return None

    if len(code) == 3:
        level = IndonesiaRoadLevel.PROVINSI
    elif len(code) in (1, 2):
        names = [road_names] if isinstance(road_names, str) else (road_names or [])
        names_lower = [(name or '').lower() for name in names]
        if force_tol or any(kw.lower() in name_lower
                            for name_lower in names_lower for kw in tol_keywords):
            level = IndonesiaRoadLevel.TOL
        else:
            level = IndonesiaRoadLevel.NASIONAL
    else:
        return None

    if region_code is None:
        for text in province_texts:
            if text is None:
                continue
            # 允许直接传省级地区代码（如 '16'）
            if text in INDONESIA_PROVINCE_CODE_MAP.values():
                region_code = text
                break
            region_code = get_indonesia_province_code(text)
            if region_code:
                break

    return IndonesiaRoadInfo(level=level, code=code, region_code=region_code)
