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


def get_field_value(row: dict, field: str, lang: str) -> str:
    """按语言读取 CSV 字段值。

    主语言 zh 以无后缀列为准，列缺失或为空时回退 _zh 后缀列（兼容两种列名）；
    副语言按标准后缀列读取，列缺失或为空返回空串。
    """
    candidates = [f'{field}{get_field_suffix(lang)}']
    if lang == 'zh':
        candidates.append(f'{field}_zh')
    for key in candidates:
        value = row.get(key)
        if value:
            return value
    return ''
