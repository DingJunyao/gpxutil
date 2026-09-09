from enum import Enum


class Region(Enum):
    """道路编号解析与路牌样式的地区体系"""
    CN = 'cn'
    ID = 'id'


# 各地区默认语言集：(主语言, [副语言...])
REGION_DEFAULT_LANGUAGES = {
    Region.CN: ('zh', ['en']),
    Region.ID: ('zh', ['id', 'en']),
}


def get_default_languages(region: Region) -> tuple[str, list[str]]:
    return REGION_DEFAULT_LANGUAGES[region]


# CSV 字段后缀：语言代码 -> 列名后缀（主语言 zh 无后缀，即 province/city/area/road_name）
LANG_FIELD_SUFFIX = {
    'zh': '',
    'id': '_id',
    'en': '_en',
}


def get_field_suffix(lang: str) -> str:
    if lang not in LANG_FIELD_SUFFIX:
        raise ValueError(f'Unknown language code: {lang}')
    return LANG_FIELD_SUFFIX[lang]
