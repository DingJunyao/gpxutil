"""印尼道路与行政区划相关数据与逻辑"""
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, unique

# 印尼省份代码（ISO 3166-2:ID 两位代码）：印尼语省名（CSV province_id 字段）与中文省名（CSV province 字段）双键
INDONESIA_PROVINCE_CODE_MAP = {
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
    province_code: str | None  # 省份代码，色带显示用（如 '35'）


def parse_indonesia_road_num(
        road_num: str | None, road_name: str | None,
        province_texts: Sequence[str | None], tol_keywords: list[str]
) -> IndonesiaRoadInfo | None:
    """
    解析印尼道路编号。
    :param road_num: CSV road_num 字段，如 '3'、'023'、'35-024'；空则无盾牌
    :param road_name: CSV road_name 字段（中文），用于 TOL 关键词判断
    :param province_texts: 候选省份文本（印尼语名、中文名，可为 None），按顺序查代码
    :param tol_keywords: TOL 判定关键词（如 ['收费', 'Tol']）
    :return: 解析结果；无法识别返回 None
    """
    if not road_num:
        return None
    road_num = road_num.strip()

    province_code = None
    if '-' in road_num:
        # '35-024'：连字符前为省代码；须命中省份代码表才作为省码，
        # 否则（含 'abc-024'、'99-024'、'-024' 等）回退到下方 province_texts 查找
        embedded, code = road_num.split('-', 1)
        embedded, code = embedded.strip(), code.strip()
        if embedded in INDONESIA_PROVINCE_CODE_MAP.values():
            province_code = embedded
    else:
        code = road_num.strip()

    # 仅接受 ASCII 数字，'３'（全角）等 Unicode 数字视为无法识别
    if not (code.isascii() and code.isdigit()):
        return None

    if len(code) == 3:
        level = IndonesiaRoadLevel.PROVINSI
    elif len(code) in (1, 2):
        name_lower = (road_name or '').lower()
        if any(kw.lower() in name_lower for kw in tol_keywords):
            level = IndonesiaRoadLevel.TOL
        else:
            level = IndonesiaRoadLevel.NASIONAL
    else:
        return None

    if province_code is None:
        for text in province_texts:
            province_code = get_indonesia_province_code(text)
            if province_code:
                break

    return IndonesiaRoadInfo(level=level, code=code, province_code=province_code)
