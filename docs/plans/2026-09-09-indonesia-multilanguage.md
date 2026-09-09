# 印尼多语言适配实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 gpxutil 增加印尼（`--region id`）道路盾牌与中/印尼/英三行覆盖层、多语言 timeline 输出，并为后续地区扩展预留 Region 抽象。

**Architecture:** Region（`cn`/`id`）决定道路编号解析与路牌体系；语言集（主语言+副语言列表）决定文本行。`Road` 子类按 Region 分派，印尼盾牌由 `id_sheild.svg` 模板 + 元素 bbox 推导布局生成。详见设计文档 `docs/plans/2026-09-09-indonesia-multilanguage-design.md`。

**Tech Stack:** Python 3.14、pytest 9、svgwrite、svgpathtools、fontTools、PIL。

**运行环境：** 所有命令在 `d:/code/gpxutil` 下执行，Python 用 `./venv/Scripts/python.exe -m pytest`。字体文件 `asset/font/ClearviewHwy1W.ttf`、`ClearviewHwy2W.ttf` 已存在。测试数据用真实印尼 CSV：`E:/project/recorded/20260829-印尼赛伍瀑布-泗水/2026-08-29 15 49 16.csv`。

**注意：** 本计划不含 git 提交步骤（用户全局规范：未主动要求不提交）。每个任务完成后是否提交由用户决定。

---

### Task 1: Region 抽象与语言集默认配置

**Files:**
- Create: `src/gpxutil/models/region.py`
- Test: `tests/test_region.py`

**Step 1: 写失败测试**

```python
# tests/test_region.py
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
```

**Step 2: 运行确认失败**

Run: `./venv/Scripts/python.exe -m pytest tests/test_region.py -v`
Expected: FAIL（ModuleNotFoundError: src.gpxutil.models.region）

**Step 3: 最小实现**

```python
# src/gpxutil/models/region.py
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
```

**Step 4: 运行确认通过**

Run: `./venv/Scripts/python.exe -m pytest tests/test_region.py -v`
Expected: PASS

---

### Task 2: 印尼省份代码映射

**Files:**
- Create: `src/gpxutil/models/indonesia.py`
- Test: `tests/test_indonesia_province.py`

**Step 1: 写失败测试**

```python
# tests/test_indonesia_province.py
from src.gpxutil.models.indonesia import INDONESIA_PROVINCE_CODE_MAP, get_indonesia_province_code


def test_province_code_indonesian_name():
    assert get_indonesia_province_code('Provinsi Jawa Timur') == '35'
    assert get_indonesia_province_code('Provinsi Bali') == '51'


def test_province_code_chinese_name():
    assert get_indonesia_province_code('东爪哇省') == '35'


def test_province_code_unknown():
    assert get_indonesia_province_code('未知省份') is None
    assert get_indonesia_province_code(None) is None


def test_map_complete():
    # 印尼 38 省（含 2022 年新设的巴布亚四省）
    assert len(INDONESIA_PROVINCE_CODE_MAP) >= 38 * 2
```

**Step 2: 运行确认失败**

Run: `./venv/Scripts/python.exe -m pytest tests/test_indonesia_province.py -v`
Expected: FAIL

**Step 3: 最小实现**

```python
# src/gpxutil/models/indonesia.py
"""印尼道路与行政区划相关数据与逻辑"""

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
```

**Step 4: 运行确认通过**

Run: `./venv/Scripts/python.exe -m pytest tests/test_indonesia_province.py -v`
Expected: PASS

---

### Task 3: 印尼道路等级与编号解析

**Files:**
- Modify: `src/gpxutil/models/indonesia.py`（追加）
- Test: `tests/test_indonesia_road.py`（新建）

**Step 1: 写失败测试**

```python
# tests/test_indonesia_road.py
from dataclasses import fields

from src.gpxutil.models.indonesia import IndonesiaRoadLevel, IndonesiaRoadInfo, parse_indonesia_road_num

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


def test_provinsi_no_province_anywhere():
    info = parse_indonesia_road_num('023', '某路', [], TOL_KEYWORDS)
    assert info.province_code is None


def test_empty_road_num():
    assert parse_indonesia_road_num('', '某路', PROVINCES, TOL_KEYWORDS) is None
    assert parse_indonesia_road_num(None, '某路', PROVINCES, TOL_KEYWORDS) is None
```

**Step 2: 运行确认失败**

Run: `./venv/Scripts/python.exe -m pytest tests/test_indonesia_road.py -v`
Expected: FAIL

**Step 3: 最小实现**（追加到 `models/indonesia.py`）

```python
from dataclasses import dataclass
from enum import Enum, unique


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
        province_texts: list[str], tol_keywords: list[str]
) -> IndonesiaRoadInfo | None:
    """
    解析印尼道路编号。
    :param road_num: CSV road_num 字段，如 '3'、'023'、'35-024'；空则无盾牌
    :param road_name: CSV road_name 字段（中文），用于 TOL 关键词判断
    :param province_texts: 候选省份文本（印尼语名、中文名），按顺序查代码
    :param tol_keywords: TOL 判定关键词（如 ['收费', 'Tol']）
    :return: 解析结果；无法识别返回 None
    """
    if not road_num:
        return None
    road_num = road_num.strip()

    province_code = None
    if '-' in road_num:
        # '35-024'：连字符前为省代码
        embedded, code = road_num.split('-', 1)
        province_code = embedded
    else:
        code = road_num

    if not code.isdigit():
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
```

**Step 4: 运行确认通过**

Run: `./venv/Scripts/python.exe -m pytest tests/test_indonesia_road.py -v`
Expected: PASS

---

### Task 4: IndonesiaRoad 类

**Files:**
- Modify: `src/gpxutil/models/road.py`
- Test: `tests/test_indonesia_road.py`（追加）

**Step 1: 写失败测试**（追加到 tests/test_indonesia_road.py）

```python
from src.gpxutil.models.road import IndonesiaRoad
from src.gpxutil.models.indonesia import IndonesiaRoadLevel


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
```

**Step 2: 运行确认失败**

Run: `./venv/Scripts/python.exe -m pytest tests/test_indonesia_road.py::test_indonesia_road_class -v`
Expected: FAIL（ImportError: IndonesiaRoad）

**Step 3: 最小实现**（追加到 `models/road.py`）

```python
from src.gpxutil.models.indonesia import IndonesiaRoadLevel, parse_indonesia_road_num


class IndonesiaRoad(Road):
    def __init__(self, road_num: str = None, road_name: str = None, province_texts: list[str] = None):
        """
        :param road_num: CSV road_num 字段，如 '3'、'023'、'35-024'
        :param road_name: CSV road_name 字段（中文），用于 TOL 关键词判断
        :param province_texts: 候选省份文本（印尼语名、中文名），用于查省份代码
        """
        from src.gpxutil.core.config import CONFIG_HANDLER
        self.name = road_name
        self.english_name = None
        self.road_num = road_num
        info = parse_indonesia_road_num(
            road_num, road_name, province_texts or [],
            CONFIG_HANDLER.config.traffic_sign.indonesia_road_sign.tol_keywords
        )
        self.level: IndonesiaRoadLevel | None = info.level if info else None
        self.code: str | None = info.code if info else None
        self.province_code: str | None = info.province_code if info else None
        self.have_sign = info is not None

    def to_svg(self):
        from src.gpxutil.utils.svg_gen import generate_indonesia_shield
        return generate_indonesia_shield(self.code, self.level, self.province_code)

    def to_svg_file(self, path: str):
        self.to_svg().saveas(path)
```

**Step 4: 运行确认通过**

Run: `./venv/Scripts/python.exe -m pytest tests/test_indonesia_road.py -v`
Expected: PASS（注意：`test_indonesia_road_class` 依赖 Task 5 的配置与 Task 6 的生成器，本步骤中该测试仍会 FAIL——将其移到 Task 6 后再跑。本条见 Task 6 说明）

---

### Task 5: 配置模型扩展

**Files:**
- Modify: `src/gpxutil/models/config.py`
- Modify: `src/gpxutil/core/config.py`
- Modify: `config/conf.example.yaml`
- Test: `tests/test_config.py`（新建）

**Step 1: 写失败测试**

```python
# tests/test_config.py
from src.gpxutil.core.config import CONFIG_HANDLER


def test_indonesia_road_sign_config():
    cfg = CONFIG_HANDLER.config.traffic_sign.indonesia_road_sign
    assert cfg.template_path.endswith('id_sheild.svg')
    assert cfg.tol_keywords == ['收费', 'Tol']
    assert cfg.font.upper.endswith('ClearviewHwy1W.ttf')
    assert cfg.font.upper_height == 45
    assert cfg.font.lower.endswith('ClearviewHwy2W.ttf')
    assert cfg.font.lower_height == 135


def test_color_blue():
    assert CONFIG_HANDLER.config.traffic_sign.color.blue == '#003E86'


def test_area_lines_config():
    lines = CONFIG_HANDLER.config.video_info_layer.frame.area.lines
    assert len(lines) == 3
    assert lines[0].font_size == 64
    assert lines[1].font_size == 44
    assert lines[2].font_size == 44
    assert lines[0].y < lines[1].y < lines[2].y
```

**Step 2: 运行确认失败**

Run: `./venv/Scripts/python.exe -m pytest tests/test_config.py -v`
Expected: FAIL（KeyError / AttributeError）

**Step 3: 实现**

3a. `models/config.py`：

```python
@dataclass
class ColorConfig:
    red: str
    white: str
    yellow: str
    black: str
    green: str
    blue: str


@dataclass
class IndonesiaRoadSignFontConfig:
    upper: str           # 色带小字字体路径（1-W）
    upper_height: int    # 色带小字高度（模板 viewBox 坐标）
    lower: str           # 大字字体路径（2-W）
    lower_height: int    # 大字高度（模板 viewBox 坐标）


@dataclass
class IndonesiaRoadSignConfig:
    template_path: str
    tol_keywords: list[str]
    font: IndonesiaRoadSignFontConfig


@dataclass
class TrafficSignConfig:
    color: ColorConfig
    font_path: FontPathConfig
    way_num_pad: WayNumPadConfig
    expwy_code_sign: ExpwyCodeSignConfig
    indonesia_road_sign: IndonesiaRoadSignConfig


@dataclass
class VideoInfoLayerTextLineConfig:
    """覆盖层一行文本的位置与字号"""
    x: float
    y: float
    font_size: int


@dataclass
class VideoInfoLayerAreaConfig:
    lines: list[VideoInfoLayerTextLineConfig]


@dataclass
class VideoInfoLayerRoadConfig:
    x: int
    middle_y: int
    sign: VideoInfoLayerRoadSignConfig
    lines: list[VideoInfoLayerTextLineConfig]  # 只含 y 与 font_size，x 用上面的 x
```

3b. `core/config.py` `parse_config`：

- `color` 增加 `blue=config_raw['traffic_sign']['color']['blue']`
- `traffic_sign` 增加：

```python
indonesia_road_sign = IndonesiaRoadSignConfig(
    template_path=config_raw['traffic_sign']['indonesia_road_sign']['template'],
    tol_keywords=config_raw['traffic_sign']['indonesia_road_sign']['tol_keywords'],
    font=IndonesiaRoadSignFontConfig(
        upper=config_raw['traffic_sign']['indonesia_road_sign']['font']['upper'],
        upper_height=config_raw['traffic_sign']['indonesia_road_sign']['font']['upper_height'],
        lower=config_raw['traffic_sign']['indonesia_road_sign']['font']['lower'],
        lower_height=config_raw['traffic_sign']['indonesia_road_sign']['font']['lower_height']
    )
)
```

- `video_info_layer_area` / `video_info_layer_road` 改行列表：

```python
video_info_layer_area = VideoInfoLayerAreaConfig(
    lines=[VideoInfoLayerTextLineConfig(**line)
           for line in config_raw['video_info_layer']['frame']['area']['lines']]
)
video_info_layer_road = VideoInfoLayerRoadConfig(
    x=config_raw['video_info_layer']['frame']['road']['x'],
    middle_y=config_raw['video_info_layer']['frame']['road']['middle_y'],
    sign=video_info_layer_road_sign,
    lines=[VideoInfoLayerTextLineConfig(**line)
           for line in config_raw['video_info_layer']['frame']['road']['lines']]
)
```

3c. `config/conf.example.yaml`（traffic_sign 节）：

```yaml
traffic_sign:
  color:
    red: '#B5273C'
    white: '#FFFFFF'
    yellow: '#FFCD00'
    black: '#000000'
    green: '#006E55'
    blue: '#003E86'
  indonesia_road_sign:
    template: asset/template/id_sheild.svg
    tol_keywords: ['收费', 'Tol']
    font:
      upper: asset/font/ClearviewHwy1W.ttf
      upper_height: 45
      lower: asset/font/ClearviewHwy2W.ttf
      lower_height: 135
```

`video_info_layer.frame` 的 `area`/`road` 改为行列表（初始值，实现时实测微调 y）：

```yaml
    area:
      lines:
        - {x: 192, y: 1924, font_size: 64}
        - {x: 192, y: 1964, font_size: 44}
        - {x: 192, y: 2006, font_size: 44}
    road:
      x: 1464
      middle_y: 1988
      sign: {width: 126, height: 128, space: 24, char_space: 48}
      lines:
        - {y: 1924, font_size: 64}
        - {y: 1964, font_size: 44}
        - {y: 2006, font_size: 44}
```

**注意：** `conf.example.yaml` 是示例，实际运行读取 `config/conf.yaml`（用户私有，未在 git 中确认）。实现时检查 `config/conf.yaml` 是否已存在并同步新字段；缺失时 `parse_config` 直接 KeyError 属预期行为（与现状一致）。

**Step 4: 运行确认通过**

Run: `./venv/Scripts/python.exe -m pytest tests/test_config.py -v`
Expected: PASS

---

### Task 6: 印尼盾牌 SVG 生成器

**Files:**
- Modify: `src/gpxutil/utils/svg_gen.py`
- Test: `tests/test_svg_gen_indonesia.py`（新建）

**Step 1: 写失败测试**

```python
# tests/test_svg_gen_indonesia.py
import xml.etree.ElementTree as ET

from src.gpxutil.models.indonesia import IndonesiaRoadLevel
from src.gpxutil.utils.svg_gen import generate_indonesia_shield


def _shapes(dwg) -> list:
    svg = ET.fromstring(dwg.tostring())
    return [c for c in svg if c.tag.endswith('polygon') or c.tag.endswith('path')]


def test_nasional_shield():
    dwg = generate_indonesia_shield('3', IndonesiaRoadLevel.NASIONAL, '35')
    svg = ET.fromstring(dwg.tostring())
    # head 色带为红色
    head = svg.find(".//*[@id='head']")
    assert head is not None
    assert head.get('fill') == '#B5273C'


def test_provinsi_shield_blue():
    dwg = generate_indonesia_shield('024', IndonesiaRoadLevel.PROVINSI, '35')
    svg = ET.fromstring(dwg.tostring())
    head = svg.find(".//*[@id='head']")
    assert head.get('fill') == '#003E86'


def test_text_paths_present():
    dwg = generate_indonesia_shield('3', IndonesiaRoadLevel.NASIONAL, '35')
    svg = ET.fromstring(dwg.tostring())
    paths = svg.findall('.//{http://www.w3.org/2000/svg}path')
    # 背景 + 色带大字（'3'，1 个字符）+ 色带小字（'NASIONAL 35'，11 个字符）
    assert len(paths) >= 1 + 1 + 11


def test_no_province_code_banner_text():
    # 无省码时色带只有等级词（'TOL' 3 字符）
    dwg = generate_indonesia_shield('8', IndonesiaRoadLevel.TOL, None)
    svg = ET.fromstring(dwg.tostring())
    paths = svg.findall('.//{http://www.w3.org/2000/svg}path')
    assert len(paths) >= 1 + 1 + 3
```

**Step 2: 运行确认失败**

Run: `./venv/Scripts/python.exe -m pytest tests/test_svg_gen_indonesia.py -v`
Expected: FAIL（ImportError: generate_indonesia_shield）

**Step 3: 实现**（追加到 `svg_gen.py`）

```python
import re
import xml.etree.ElementTree as ET  # 已 import

from src.gpxutil.models.indonesia import IndonesiaRoadLevel


# 印尼盾牌：等级 -> 色带文字与颜色
INDONESIA_LEVEL_BANNER_TEXT = {
    IndonesiaRoadLevel.NASIONAL: 'NASIONAL',
    IndonesiaRoadLevel.TOL: 'TOL',
    IndonesiaRoadLevel.PROVINSI: 'PROVINSI',
}


def calculate_centered_scaled_char_info(code: str, center_x: float, center_y: float,
                                        height: float, font: str) -> list[Path]:
    """
    按固定高度缩放一段文字，并使其水平居中于 center_x、垂直居中于 center_y。
    与 calculate_scaled_char_info 共用 char_to_svg_path 底层。
    """
    scaled_char_path_list = []
    scaled_char_width_list = []
    for i in code:
        paths_char = char_to_svg_path(font, i)
        char_minx, char_maxx, char_miny, char_maxy = paths_char.bbox()
        ratio = height / (char_maxy - char_miny)
        scaled_path_char = paths_char.scaled(ratio)
        scaled_char_minx, scaled_char_maxx, scaled_char_miny, scaled_char_maxy = scaled_path_char.bbox()
        scaled_path_char = scaled_path_char.translated(complex(-scaled_char_minx, -scaled_char_miny))
        scaled_char_width_list.append(scaled_char_maxx - scaled_char_minx)
        scaled_char_path_list.append(scaled_path_char)
    total_width = sum(scaled_char_width_list)
    start_x = center_x - total_width / 2
    char_x = start_x
    char_y = center_y - height / 2
    char_pos_list = []
    for i, char_width in enumerate(scaled_char_width_list):
        if i != 0:
            char_x += scaled_char_width_list[i - 1]
        char_pos_list.append((char_x, char_y))
    return [path.translated(complex(*pos)) for path, pos in zip(scaled_char_path_list, char_pos_list)]


def get_element_bbox_by_id(svg_path: str, element_id: str):
    """解析 SVG 模板，取指定 id 元素的 bbox（支持 polygon/path）。"""
    tree = ET.parse(svg_path)
    root = tree.getroot()
    elem = root.find(f".//*[@id='{element_id}']")
    if elem is None:
        return None
    if elem.tag.endswith('polygon'):
        nums = [float(n) for n in re.split(r'[\s,]+', elem.get('points', '').strip()) if n]
        xs, ys = nums[0::2], nums[1::2]
        return min(xs), min(ys), max(xs), max(ys)
    return None


def generate_indonesia_shield(code: str, road_level: IndonesiaRoadLevel,
                              province_code: str | None) -> Drawing:
    """生成印尼六边形道路盾牌。模板布局由元素 bbox 推导，不硬编码坐标。"""
    set_const()
    cfg = CONFIG_HANDLER.config.traffic_sign.indonesia_road_sign

    # 色带颜色：NASIONAL/TOL 红，PROVINSI 蓝
    head_fill = RED if road_level in (IndonesiaRoadLevel.NASIONAL, IndonesiaRoadLevel.TOL) \
        else CONFIG_HANDLER.config.traffic_sign.color.blue

    # 色带文字：等级词 + 省码
    banner_text = INDONESIA_LEVEL_BANNER_TEXT[road_level]
    if province_code:
        banner_text += f' {province_code}'

    # 模板尺寸与 head 色带 bbox
    width, height = get_svg_dimensions(cfg.template_path)
    head_bbox = get_element_bbox_by_id(cfg.template_path, 'head')
    if head_bbox is None:
        raise ValueError(f'Template {cfg.template_path} has no element with id "head"')
    head_center_y = (head_bbox[1] + head_bbox[3]) / 2
    # 白色区：色带底边与盾牌底边之间
    lower_center_y = (head_bbox[3] + height) / 2
    center_x = width / 2

    paths, attributes = svg2paths(cfg.template_path)

    dwg = svgwrite.Drawing('output.svg', size=(f'{width}', f'{height}'))
    # 背景 path 原样绘制（模板自身颜色）；head polygon 单独按等级上色
    for path, attr in zip(paths, attributes):
        fill = attr.get('class') or 'none'
        dwg.add(dwg.path(d=path.d(), fill=fill if fill not in ('none',) else 'none'))
    dwg.add(dwg.polygon(points=head_bbox_points(cfg.template_path, 'head'), id='head', fill=head_fill))

    banner_paths = calculate_centered_scaled_char_info(
        banner_text, center_x, head_center_y, cfg.font.upper_height, cfg.font.upper)
    code_paths = calculate_centered_scaled_char_info(
        code, center_x, lower_center_y, cfg.font.lower_height, cfg.font.lower)

    for path in banner_paths:
        dwg.add(dwg.path(d=path.d(), fill=WHITE))
    for path in code_paths:
        dwg.add(dwg.path(d=path.d(), fill=BLACK))
    return dwg
```

实现说明：`head` 是 polygon，`svg2paths` 不解析 polygon，需单独从模板 XML 取 points。补一个取 points 原串的小函数：

```python
def get_element_points_by_id(svg_path: str, element_id: str) -> str:
    tree = ET.parse(svg_path)
    root = tree.getroot()
    elem = root.find(f".//*[@id='{element_id}']")
    return elem.get('points') if elem is not None else None
```

`dwg.polygon(points=..., ...)` 的 points 直接传原字符串。

**Step 4: 运行确认通过**

Run: `./venv/Scripts/python.exe -m pytest tests/test_svg_gen_indonesia.py tests/test_indonesia_road.py -v`
Expected: PASS（Task 4 的 `test_indonesia_road_class` 至此才可运行）

**Step 5: 人工验证**

Run: `./venv/Scripts/python.exe -c "from src.gpxutil.models.road import IndonesiaRoad; IndonesiaRoad('35-024', '图卢斯阿尤大街', ['Provinsi Jawa Timur']).to_svg_file('out/test_id_shield.svg')"`
Expected: 生成 `out/test_id_shield.svg`，打开查看：六边形红头（PROVINSI 场景为蓝头）、色带白色文字"PROVINSI 35"、白区黑色大字"024"，均居中。

---

### Task 7: create_pic CSV 解析按 Region 分派

**Files:**
- Modify: `src/gpxutil/utils/create_pic.py`
- Test: `tests/test_create_pic_multilang.py`（新建）

**Step 1: 写失败测试**

```python
# tests/test_create_pic_multilang.py
from src.gpxutil.models.region import Region
from src.gpxutil.utils.create_pic import build_area_texts, build_road_texts, parse_road_signs

CN_ROW = {
    'province': '河南省', 'city': '三门峡市', 'area': '渑池县',
    'province_en': 'Henan Province', 'city_en': 'Sanmenxia City', 'area_en': 'Mianchi County',
    'road_num': 'G310', 'road_name': '黄河路', 'road_name_en': 'Huanghe Rd.',
}
ID_ROW = {
    'province': '东爪哇省', 'city': '玛琅县', 'area': '安佩尔加丁镇',
    'province_id': 'Provinsi Jawa Timur', 'city_id': 'Kabupaten Malang', 'area_id': 'Kecamatan Ampelgading',
    'province_en': 'Province of East Java', 'city_en': 'Malang Regency', 'area_en': 'Ampelgading District',
    'road_num': '35-024', 'road_name': '图卢斯阿尤大街',
    'road_name_id': 'Jl. Raya Tulus Ayu', 'road_name_en': 'Tulus Ayu Main Rd.',
}


def test_build_area_texts_cn():
    assert build_area_texts(CN_ROW, Region.CN) == ['河南省 三门峡市 渑池县',
                                                    'Mianchi County, Sanmenxia City, Henan Province']


def test_build_area_texts_id():
    assert build_area_texts(ID_ROW, Region.ID) == ['东爪哇省 玛琅县 安佩尔加丁镇',
                                                    'Kecamatan Ampelgading, Kabupaten Malang, Provinsi Jawa Timur',
                                                    'Ampelgading District, Malang Regency, Province of East Java']


def test_build_road_texts_cn():
    assert build_road_texts(CN_ROW, Region.CN) == ['黄河路', 'Huanghe Rd.']


def test_build_road_texts_id():
    assert build_road_texts(ID_ROW, Region.ID) == ['图卢斯阿尤大街', 'Jl. Raya Tulus Ayu', 'Tulus Ayu Main Rd.']


def test_parse_road_signs_cn():
    signs = parse_road_signs(CN_ROW, Region.CN)
    assert len(signs) == 1
    assert signs[0] is not None


def test_parse_road_signs_id():
    signs = parse_road_signs(ID_ROW, Region.ID)
    assert len(signs) == 1
    assert signs[0] is not None


def test_parse_road_signs_empty():
    assert parse_road_signs({'road_num': ''}, Region.CN) == []
```

**Step 2: 运行确认失败**

Run: `./venv/Scripts/python.exe -m pytest tests/test_create_pic_multilang.py -v`
Expected: FAIL（ImportError）

**Step 3: 实现**（追加到 `create_pic.py`，并把 `read_csv_with_additional_info` 中 road_sign 逻辑替换为调用 `parse_road_signs`）

```python
from src.gpxutil.models.region import Region, get_default_languages, get_field_suffix
from src.gpxutil.models.road import IndonesiaRoad


def build_area_texts(row: dict, region: Region) -> list[str]:
    """按语言集组装区域文本行：[主语言, 副语言...]，空行剔除"""
    primary, secondary = get_default_languages(region)
    texts = []
    # 主语言 zh：空格正序拼接
    if primary == 'zh':
        texts.append(' '.join([i for i in [row['province'], row['city'], row['area']] if i]))
    else:
        texts.append(', '.join([i for i in [row[f'area{get_field_suffix(primary)}'],
                                            row[f'city{get_field_suffix(primary)}'],
                                            row[f'province{get_field_suffix(primary)}']] if i]))
    # 副语言：逗号倒序拼接（同现状英文语序）
    for lang in secondary:
        text = ', '.join([i for i in [row[f'area{get_field_suffix(lang)}'],
                                      row[f'city{get_field_suffix(lang)}'],
                                      row[f'province{get_field_suffix(lang)}']] if i])
        texts.append(text)
    return [t for t in texts if t]


def build_road_texts(row: dict, region: Region) -> list[str]:
    """按语言集组装路名文本行：[主语言, 副语言...]，空行剔除"""
    primary, secondary = get_default_languages(region)
    langs = [primary] + secondary
    texts = [row[f'road_name{get_field_suffix(lang)}'] or '' for lang in langs]
    return [t for t in texts if t]


def parse_road_signs(row: dict, region: Region) -> list[Drawing]:
    """按 Region 解析 road_num 为路牌 Drawing 列表"""
    global road_num_svg_cache
    road_num = row.get('road_num') or ''
    if not road_num:
        return []
    sign_list = []
    for road_sign in road_num.split(','):
        if road_sign in road_num_svg_cache:
            sign_list.append(road_num_svg_cache[road_sign])
            continue
        if region == Region.ID:
            road = IndonesiaRoad(road_sign, row.get('road_name'),
                                 [row.get('province_id'), row.get('province')])
            drawing = road.to_svg() if road.have_sign else None
        else:
            # 中国现状逻辑
            if road_sign[0] in string.ascii_uppercase:
                if len(road_sign) == 4:
                    drawing = generate_way_num_pad(road_sign)
                else:
                    drawing = generate_expwy_pad(road_sign)
            else:
                drawing = generate_expwy_pad(road_sign[1:], province=road_sign[0])
        if drawing is not None:
            road_num_svg_cache[road_sign] = drawing
            sign_list.append(drawing)
    return sign_list
```

改造 `read_csv_with_additional_info`（签名加 `region: Region = Region.CN`）：

```python
def read_csv_with_additional_info(path, start_index=0, end_index=-1, ..., region: Region = Region.CN):
    ...
        new_row['area_texts'] = build_area_texts(row, region)
        new_row['road_texts'] = build_road_texts(row, region)
        new_row['road_sign_svg'] = parse_road_signs(row, region)
    ...
```

（`full_area`/`full_area_en` 键由 `area_texts` 取代；`road_name`/`road_name_en` 由 `road_texts` 取代。`generate_pic_from_processed_dict_list` 的调用处同步更新，见 Task 8。）

**Step 4: 运行确认通过**

Run: `./venv/Scripts/python.exe -m pytest tests/test_create_pic_multilang.py -v`
Expected: PASS

---

### Task 8: generate_pic 多行渲染布局

**Files:**
- Modify: `src/gpxutil/utils/create_pic.py`
- Test: `tests/test_create_pic_multilang.py`（追加）

**Step 1: 写失败测试**（追加）

```python
from src.gpxutil.utils.create_pic import generate_pic


def test_generate_pic_three_lines():
    img = generate_pic(
        area_texts=['东爪哇省 玛琅县 安佩尔加丁镇',
                    'Kecamatan Ampelgading, Kabupaten Malang, Provinsi Jawa Timur',
                    'Ampelgading District, Malang Regency, Province of East Java'],
        road_texts=['图卢斯阿尤大街', 'Jl. Raya Tulus Ayu', 'Tulus Ayu Main Rd.'],
        road_sign_list=None, compass_angle=90, used_route=1.0, used_time=60,
        remain_route=2.0, remain_time=120, altitude=500, speed=40
    )
    assert img.size == (3840, 2160)
    img.close()


def test_generate_pic_two_lines_cn_backcompat():
    img = generate_pic(
        area_texts=['河南省 三门峡市 渑池县', 'Mianchi County, Sanmenxia City, Henan Province'],
        road_texts=['黄河路', 'Huanghe Rd.'],
        road_sign_list=None, compass_angle=None, used_route=None, used_time=None,
        remain_route=None, remain_time=None, altitude=None, speed=None
    )
    assert img.size == (3840, 2160)
    img.close()
```

**Step 2: 运行确认失败**

Run: `./venv/Scripts/python.exe -m pytest tests/test_create_pic_multilang.py::test_generate_pic_three_lines -v`
Expected: FAIL（TypeError: unexpected keyword argument 'area_texts'）

**Step 3: 实现**

`generate_pic` 签名与主体改为：

```python
def generate_pic(area_texts, road_texts, road_sign_list, compass_angle, used_route, used_time,
                 remain_route, remain_time, altitude, speed):
    """
    :param area_texts: 区域文本行列表，[0]=主语言（大字），[1:]=副语言（小字）
    :param road_texts: 路名文本行列表，同上
    """
    image = Image.new(mode='RGBA', size=image_size)
    draw_table = ImageDraw.Draw(im=image)

    # 当前区域：主语言大字 + 副语言小字逐行
    area_lines = CONFIG_HANDLER.config.video_info_layer.frame.area.lines
    for text, line in zip(area_texts, area_lines):
        font = big_font if line.font_size >= 64 else small_font
        draw_table.text(xy=(line.x, line.y), text=text, fill=font_color, font=font)

    # 当前道路（路牌 SVG 同现状绘制，offset 逻辑不变）
    road_sign_offset = road_xy[0]
    if road_sign_list:
        ...  # 现状代码不变
        road_sign_offset = road_sign_offset - road_sign_space + road_sign_char_space

    # 路名：主语言大字 + 副语言小字逐行
    road_lines = CONFIG_HANDLER.config.video_info_layer.frame.road.lines
    max_right_x = road_sign_offset
    for text, line in zip(road_texts, road_lines):
        font = big_font if line.font_size >= 64 else small_font
        draw_table.text(xy=(road_sign_offset, line.y), text=text, fill=font_color, font=font)
        width = draw_table.textlength(text=text, font=font)
        max_right_x = max(max_right_x, road_sign_offset + width)

    # 指南针避让：取所有行最大右边界（替换原 road_zh_right_x/road_en_right_x 逻辑）
    compass_final_xy = compass_xy
    if max_right_x + road_sign_char_space > compass_xy[0]:
        compass_final_xy = (math.ceil(max_right_x + road_sign_char_space), compass_xy[1])
    ...  # 其余（指南针、里程、海拔、速度）不变
```

`generate_pic_from_processed_dict_list` 调用处改为：

```python
        img = generate_pic(
            area_texts=row['area_texts'], road_texts=row['road_texts'],
            road_sign_list=row['road_sign_svg'],
            compass_angle=row['course'],
            used_route=row['distance'], used_time=row['elapsed_time'],
            remain_route=row['remain_distance'], remain_time=row['remain_time'],
            altitude=row['elevation'], speed=row['speed']
        )
```

模块顶部硬编码坐标常量（`area_chinese_xy`、`area_english_xy`、`road_chinese_y`、`road_english_y`）删除，`road_xy` 等保留（`road_xy`、`compass_xy` 等右侧元素坐标暂不动，行 y 改由配置提供）。

**Step 4: 运行确认通过**

Run: `./venv/Scripts/python.exe -m pytest tests/test_create_pic_multilang.py -v`
Expected: PASS

**Step 5: 人工验证**

Run:
```bash
./venv/Scripts/python.exe -m pytest tests/test_cli_arguments.py tests/test_main_cli.py -v
```
Expected: PASS（确认无回归——旧测试不直接调用 generate_pic 参数）

---

### Task 9: CLI 接入 region 参数与主流程打通

**Files:**
- Modify: `src/gpxutil/utils/create_pic.py`（`generate_pic_from_csv` 透传 region）
- Modify: `main.py`（overlay/info 子命令 `--region`）
- Test: `tests/test_cli_arguments.py`（追加）

**Step 1: 写失败测试**（追加到 tests/test_cli_arguments.py）

```python
def test_cli_overlay_with_region_id():
    """overlay 命令接收 --region id 并透传"""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('index\n0\n')
        csv_path = f.name
    out_dir = tempfile.mkdtemp()
    with patch('main.generate_pic_from_csv') as mock_gen:
        sys.argv = ['main.py', 'overlay', csv_path, out_dir, '--region', 'id', '--end_index', '0']
        try:
            main()
            assert mock_gen.call_args.kwargs['region'] == Region.ID
        except SystemExit:
            pass
        finally:
            os.remove(csv_path)
```

**Step 2: 运行确认失败**

Run: `./venv/Scripts/python.exe -m pytest tests/test_cli_arguments.py::test_cli_overlay_with_region_id -v`
Expected: FAIL（unrecognized arguments: --region）

**Step 3: 实现**

`main.py` overlay 与 info 子命令各加：

```python
csv_parser.add_argument('--region', choices=['cn', 'id'], default='cn', help='地区：cn=中国大陆，id=印尼')
info_parser.add_argument('--region', choices=['cn', 'id'], default='cn', help='地区：cn=中国大陆，id=印尼')
```

调用处：

```python
from src.gpxutil.models.region import Region
# overlay 分支
generate_pic_from_csv(..., region=Region(args.region))
# info 分支
print(generate_road_info(input_csv_file_path, Region(args.region)))
```

`create_pic.py`：

```python
def generate_pic_from_csv(path, ..., region: Region = Region.CN):
    dict_list = read_csv_with_additional_info(path, ..., region=region)
    generate_pic_from_processed_dict_list(dict_list, crop_start, out_dir)
```

**Step 4: 运行确认通过**

Run: `./venv/Scripts/python.exe -m pytest tests/test_cli_arguments.py -v`
Expected: PASS

---

### Task 10: gen_road_info timeline 多语言

**Files:**
- Modify: `src/gpxutil/utils/gen_road_info.py`
- Test: `tests/test_gen_road_info_multilang.py`（新建）

**Step 1: 写失败测试**

```python
# tests/test_gen_road_info_multilang.py
from src.gpxutil.models.region import Region
from src.gpxutil.utils.gen_road_info import gen_single_road_code, get_info, gen_route_info


def test_indonesia_label_colors():
    assert 'red' in gen_single_road_code('3', Region.ID)
    assert 'green' in gen_single_road_code('8', Region.ID)
    assert 'blue' in gen_single_road_code('023', Region.ID)
    assert 'blue' in gen_single_road_code('35-024', Region.ID)


def test_indonesia_label_plain_code():
    # label 内为纯编号，不含省码
    text = gen_single_road_code('35-024', Region.ID)
    assert '024' in text
    assert '35-024' not in text


def test_cn_backcompat():
    assert gen_single_road_code('G310', Region.CN) == '{% label G310 red %}'
    assert gen_single_road_code('赣S22', Region.CN) == '赣 {% label S22 green %}'


def test_get_info_id_multilang(tmp_path):
    csv_path = tmp_path / 'id.csv'
    csv_path.write_text(
        'index,province,city,area,province_id,city_id,area_id,province_en,city_en,area_en,road_num,road_name,road_name_id,road_name_en\n'
        '0,东爪哇省,玛琅县,安佩尔加丁镇,Provinsi Jawa Timur,Kabupaten Malang,Kecamatan Ampelgading,'
        'Province of East Java,Malang Regency,Ampelgading District,023,图姆庞大街,Jl. Raya Tumpang,Tumpang Main Rd.\n',
        encoding='utf-8'
    )
    city_list = get_info(str(csv_path), Region.ID)
    assert len(city_list) == 1
    area = city_list[0].areas[0]
    assert area.names == {'zh': '安佩尔加丁镇', 'id': 'Kecamatan Ampelgading', 'en': 'Ampelgading District'}
    road = area.roads[0]
    assert road.names['id'] == 'Jl. Raya Tumpang'


def test_gen_route_info_id_multilang(tmp_path):
    csv_path = tmp_path / 'id.csv'
    csv_path.write_text(
        'index,province,city,area,province_id,city_id,area_id,province_en,city_en,area_en,road_num,road_name,road_name_id,road_name_en\n'
        '0,东爪哇省,玛琅县,安佩尔加丁镇,Provinsi Jawa Timur,Kabupaten Malang,Kecamatan Ampelgading,'
        'Province of East Java,Malang Regency,Ampelgading District,023,图姆庞大街,Jl. Raya Tumpang,Tumpang Main Rd.\n',
        encoding='utf-8'
    )
    city_list = get_info(str(csv_path), Region.ID)
    text = gen_route_info(city_list, Region.ID)
    assert '东爪哇省 玛琅县' in text
    assert '印尼语：Provinsi Jawa Timur · Kabupaten Malang' in text
    assert '英语：Province of East Java · Malang Regency' in text
    assert '{% label 023 blue %}' in text
    assert '  Jl. Raya Tumpang' in text
    assert '  Tumpang Main Rd.' in text
```

**Step 2: 运行确认失败**

Run: `./venv/Scripts/python.exe -m pytest tests/test_gen_road_info_multilang.py -v`
Expected: FAIL

**Step 3: 实现**

- `RoadInfo` / `AreaInfo` / `CityInfo` 增加 `names: dict[str, str]`；`read_csv` 不做语言处理（保持通用），`get_info(csv_dict_list, region)` 组装：

```python
def get_info(csv_dict_list: list[dict], region: Region = Region.CN):
    primary, secondary = get_default_languages(region)
    langs = [primary] + secondary
    ...
    area = AreaInfo(
        names={lang: csv_dict[f'area{get_field_suffix(lang)}'] or '' for lang in langs},
        roads=[RoadInfo(
            code=csv_dict['road_num'].split(',') if csv_dict['road_num'] else [],
            names={lang: csv_dict[f'road_name{get_field_suffix(lang)}'] or '' for lang in langs},
        )]
    )
```

（原 `name` 字段删除，模板处改用 `names`；`AreaInfo.__eq__`/`CityInfo.__eq__` 比较逻辑保持按主语言名等价。）

- `gen_single_road_code(road_code: str, region: Region)` 分派：

```python
INDONESIA_LABEL_COLOR = {
    IndonesiaRoadLevel.NASIONAL: 'red',
    IndonesiaRoadLevel.TOL: 'green',
    IndonesiaRoadLevel.PROVINSI: 'blue',
}


def gen_single_road_code(road_code: str, region: Region = Region.CN) -> str:
    if not road_code:
        return ""
    if region == Region.ID:
        info = parse_indonesia_road_num(road_code, None, [], [])  # label 只需等级与纯编号
        if info is None:
            return ""
        return "{% label %s %s %}" % (info.code, INDONESIA_LABEL_COLOR[info.level])
    # 中国现状逻辑原样保留
    ...
```

（注意：label 阶段无 road_name，TOL 关键词判定用不到——1-2 位数字默认 NASIONAL 红色；若 CSV 中该路为 toll，其 label 颜色在 gen_route_info 组装时由 RoadInfo 携带等级信息补充，见下。KISS：label 颜色由 `RoadInfo` 新增 `level` 字段驱动，`gen_route_info` 组装时用等级查色。实现时若简化，允许 toll 显示红色 label，此差异在最终人工验证中与用户确认。）

- `gen_route_info(city_info_list, region)` 输出多语言（主语言行 + 副语言行带前缀）：

```python
LANG_PREFIX = {'zh': '', 'id': '印尼语：', 'en': '英语：'}

CITY_TIMELINE_TEMPLATE = """{% timeline {{province}} {{city}}（视频 XX:XX） %}
{{areas_info}}
{% endtimeline %}"""
AREA_TIMELINE_TEMPLATE = """<!-- timeline {{area}}（视频 XX:XX） -->
{{area_secondary}}
{{road_info}}
<!-- endtimeline -->"""
```

副语言行拼接：`'印尼语：Provinsi Jawa Timur · Kabupaten Malang'`（区级同理）。道路行：主行 `label + 主语言路名`，副行 `  `（两个空格缩进）+ 路名。

**Step 4: 运行确认通过**

Run: `./venv/Scripts/python.exe -m pytest tests/test_gen_road_info_multilang.py -v`
Expected: PASS

**Step 5: 回归**

Run: `./venv/Scripts/python.exe -m pytest tests/ -v`
Expected: 全部 PASS

---

### Task 11: 端到端验证（真实印尼 CSV）

**Files:** 无（仅验证）

**Step 1: 生成盾牌抽查**

Run:
```bash
./venv/Scripts/python.exe -c "
from src.gpxutil.models.road import IndonesiaRoad
IndonesiaRoad('3', 'Jl. Nasional III', ['Provinsi Jawa Timur']).to_svg_file('out/id_nas3.svg')
IndonesiaRoad('8', '泗水-波龙收费公路', ['Provinsi Jawa Timur']).to_svg_file('out/id_tol8.svg')
IndonesiaRoad('023', '图姆庞大街', ['Provinsi Jawa Timur']).to_svg_file('out/id_prov23.svg')
IndonesiaRoad('35-024', '图卢斯阿尤大街', ['Provinsi Jawa Timur']).to_svg_file('out/id_prov24.svg')
"
```
Expected: 4 个 SVG 生成；人工检查颜色（红/红/蓝/蓝）与文字（大字编号、色带"等级+省码"）居中情况。

**Step 2: 生成覆盖层小样**

Run:
```bash
./venv/Scripts/python.exe -m main overlay "E:/project/recorded/20260829-印尼赛伍瀑布-泗水/2026-08-29 15 49 16.csv" out/id_overlay --region id --start_index 0 --end_index 99 --crop_start 0 --crop_end 99
```
Expected: `out/id_overlay/` 下 100 张 PNG；人工抽查 2-3 张：左上三行（中/印尼/英）、路牌为印尼盾牌、路名三行、指南针/里程正常。

**Step 3: 生成 timeline**

Run:
```bash
./venv/Scripts/python.exe -m main info "E:/project/recorded/20260829-印尼赛伍瀑布-泗水/2026-08-29 15 49 16.csv" --region id > out/id_timeline.txt
```
Expected: `out/id_timeline.txt` 含中文主行 + 印尼语/英语副行 + 印尼 label。

**Step 4: 中国回归**

Run:
```bash
./venv/Scripts/python.exe -m main overlay test/20250226132250.csv out/cn_regression --end_index 50
./venv/Scripts/python.exe -m pytest tests/ -v
```
Expected: 中国 CSV 输出与改动前一致（两行布局），全部测试 PASS。

---

## 完成标准

- [ ] `--region id` 生成印尼盾牌（NASIONAL/TOL 红、PROVINSI 蓝，色带含省码，Clearview 字体 45/135px 居中）
- [ ] 印尼覆盖层三行（中/印尼/英），中国覆盖层两行不变
- [ ] timeline 多语言逐行输出、印尼 label 颜色正确
- [ ] 全部测试 PASS（含既有 CLI 测试回归）
- [ ] 设计文档 `docs/plans/2026-09-09-indonesia-multilanguage-design.md` 与实际实现一致
