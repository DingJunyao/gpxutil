# 印尼多语言适配设计

日期：2026-09-09

## 背景与目标

工具此前仅支持中国大陆：道路模型、路牌生成（中国国标 G/S/X 体系）、覆盖层文本（中/英两行）、timeline 文本均为大陆硬编码。现需适配印尼：

1. 覆盖层在中文、英文之外增加印尼语文本行
2. 印尼道路徽标使用六边形盾牌模板（`asset/template/id_sheild.svg`）
3. 架构上为其他语言和地区预留扩展位置，新增地区成本最低

参考数据：`E:\project\recorded\20260829-印尼赛伍瀑布-泗水\2026-08-29 15 49 16.csv`（字段含 `province/city/area` 中文、`province_id/city_id/area_id` 印尼语、`province_en/city_en/area_en` 英文，路名同理）。

## 决策记录

| 决策点 | 结论 |
|---|---|
| 地区识别 | CLI 显式参数 `--region cn\|id`，默认 `cn` |
| 印尼路牌等级 | 依印尼官方规则（见下），NASIONAL/TOL 靠路名关键词区分 |
| 盾牌大字 | 纯编号（`35-024` → 大字 `024`，省码只上色带） |
| 覆盖层布局 | 主语言 64px 大字 + 副语言 44px 逐行（三行） |
| 扩展架构 | 类继承 + region 分派（OCP） |
| 改动范围 | 覆盖层 + timeline 一起适配 |
| Timeline 语言 | 自定义：一个主语言 + 若干副语言，逐行对照 |
| 印尼路牌字体 | Clearview：色带 1-W 高 45px、大字 2-W 高 135px，水平居中，垂直分别居中于色带与白色区 |

## 1. 总体架构

**核心抽象：Region（地区）+ 语言集**，两者独立：

- `Region` 决定道路编号解析规则与路牌样式体系。本次实现 `CN`（现有）与 `ID`（印尼），CLI 显式指定，默认 `cn` 向后兼容。
- 语言集决定文本显示：`primary`（主语言，大字/主行）+ `secondary`（副语言列表）。默认约定：`cn` → 主 `zh` 副 `[en]`；`id` → 主 `zh` 副 `[id, en]`。用户可覆盖。

**道路模型**（`src/gpxutil/models/road.py`）：

```
Road（基类，现状不变）
├── ChinaMainlandRoad / ChinaMainlandExpwy（现状不变）
└── IndonesiaRoad（新增）
```

`IndonesiaRoad` 持有：编号纯数字部分（如 `024`）、等级（`NASIONAL`/`TOL`/`PROVINSI`）、省份代码（如 35）。等级与省码解析在构造阶段完成，SVG 生成只消费结果。新增地区 = 新增子类 + 生成函数，不动现有类。

**路牌生成**（`src/gpxutil/utils/svg_gen.py`）：

- 新增 `generate_indonesia_shield(code, road_level, province_code)`，读取 `id_sheild.svg` 模板。
- 中国函数不动；上层加按 region 分派的工厂函数（一处 if/else）。

**数据流**（`src/gpxutil/utils/create_pic.py`）：

```
CSV → read_csv_with_additional_info（按 region 解析 road_num → Road 对象、组装多语言文本）
    → generate_pic（语言集驱动：主语言一行大字 + 每个副语言一行小字）
    → PNG 序列
```

`generate_pic` 签名从 `area_zh/area_en/road_zh/road_en` 改为 `area_texts: list[str] / road_texts: list[str]`。右侧指南针/里程/海拔布局不变。

## 2. 印尼路牌生成器

**印尼道路编号规则**（[Nomor rute - Wikipedia](https://id.m.wikipedia.org/wiki/Nomor_rute)，Perdirjenhubdat 2019 Pedoman Penomoran Rute Jalan）：路牌为六边形，白底黑字，顶部色带写等级小字 + 编号大字：

| 道路等级 | 色带颜色 | 色带小字 | 编号 |
|---|---|---|---|
| Jalan Nasional 国家公路 | 红 | NASIONAL | 1-2 位数字 |
| Jalan Tol 收费高速 | 红 | TOL | 1-2 位数字 |
| Jalan Provinsi 省道 | 蓝 | PROVINSI | 3 位数字 |

色带小字为"等级词 + 空格 + 省份代码"（如 `NASIONAL 35`）。省码来源优先级：编号内嵌（`35-024` 的 35）→ CSV `province_id`/`province` 字段经映射表查得 → 都没有则只写等级词。

**等级判定**（构造 `IndonesiaRoad` 时完成）：

| road_num | 等级 | 大字 | 色带 |
|---|---|---|---|
| `35-024` | PROVINSI | `024` | `PROVINSI 35` |
| `023`（无省码） | PROVINSI | `023` | `PROVINSI 35`（省码从 CSV 省份字段查） |
| `3`、`15`（1-2 位） | NASIONAL | `3` | `NASIONAL 35` |
| `8` 且路名含"收费"/"Tol" | TOL | `8` | `TOL 35` |
| 空 | 无盾牌，只显示路名 | — | — |

NASIONAL/TOL 编号体系相同，无法从数字区分，靠路名关键词（`tol_keywords`，默认 `['收费', 'Tol']`，可配置扩展）。

**模板利用**：`id_sheild.svg` 为白六边形背景 + 红色 `head` 色带 + 两组占位文字路径。程序生成时：

- 读背景路径原样绘制
- `head` 色带按等级覆盖颜色：NASIONAL/TOL = 红（复用配置 `color.red #B5273C`），PROVINSI = 蓝（配置新增 `color.blue #003E86`）。一份模板支持所有等级
- 文字锚点从模板元素 bbox 推导，代码不硬编码坐标，换模板自动适配

**字体制式**（模板 viewBox 坐标系，均水平居中于六边形水平中心）：

| 位置 | 字体 | 高度 | 垂直定位 |
|---|---|---|---|
| 色带小字（`NASIONAL 35`） | `ClearviewHwy1W.ttf`（1-W） | 45px | 垂直居中于色带（`head` bbox 中心） |
| 白色区大字（编号） | `ClearviewHwy2W.ttf`（2-W） | 135px | 垂直居中于白色区（`head` 底边与背景底边中点） |

排版函数：现有 `calculate_scaled_char_info` 是"固定框+起始坐标"模式；新增居中排版函数（固定高度+居中锚点），与现有函数共用字体转路径底层逻辑（DRY）。

印尼省名→代码映射表（38 省，如 `Provinsi Jawa Timur → 35`）：`INDONESIA_PROVINCE_CODE_MAP` 双键 dict（印尼语省名/中文省名）放入 `models/indonesia.py`，属印尼专属数据。

## 3. 覆盖层多语言布局与 CSV 解析

**CSV 解析**（`create_pic.py` 的 `read_csv_with_additional_info`）：

- 按 `--region` 组装文本行：
  - `cn`：主行中文 `省 市 区` + 副行英文 `区, 市, 省`（现状不变）
  - `id`：主行中文（现状拼接）+ 副行印尼语 `Kecamatan Ampelgading, Kabupaten Malang, Provinsi Jawa Timur`（从小到大，同英文语序）+ 副行英文
- 路名同理：`road_name` 主行，`road_name_id`、`road_name_en` 副行；某行全空则跳过该行
- `road_num` 解析按 region 分派到工厂函数：`cn` → 现有 `ChinaMainlandRoad` 逻辑；`id` → 构造 `IndonesiaRoad`（第 2 节规则，等级判定需读取 `road_name`）。产出仍是 `Drawing` 列表，`generate_pic` 不感知地区

**`generate_pic` 签名**：

```python
generate_pic(area_texts, road_texts, road_sign_list, ...)
# area_texts / road_texts: list[str]，[0]=主语言，[1:]=副语言
```

主语言 64px 大字、副语言 44px 小字（现有英文 48 略降，为第三行腾空间），逐行向下。行坐标从配置读取（`frame.area` / `frame.road` 改为按行配置 y 与字号，语言集有几行用前几行）；行数超过 2 行时整块上移（每多一行上移一个行距，两行布局保持原值），避免侵占视频字幕区域。具体像素值实现时实测微调。

指南针避让：取所有语言行的最大文本宽度（现状取中英两行最大，改为遍历所有行）。

CLI（`main.py`）：新增 `--region cn|id`（默认 `cn`）。印尼三行、中国两行出自同一套语言集机制，无地区专属分支。语言集当前按 region 约定固定（`REGION_DEFAULT_LANGUAGES`）；`--lang-primary` / `--lang-secondary` 语言覆盖参数留待后续实现。

## 4. Timeline 多语言适配

**数据结构**（`src/gpxutil/utils/gen_road_info.py`）：`CityInfo`/`AreaInfo`/`RoadInfo` 的单一语言字段改为多语言字段（如 `AreaInfo.names: dict[str, str]`，键为语言代码）。`get_info` 按 region 组装：中国 CSV 只有 `zh`/`en`，印尼 CSV 有 `zh`/`id`/`en`。输出顺序 = 主语言 + 副语言列表。

**输出形式**（逐行对照），副语言行带语言前缀（`印尼语：`/`英语：`，可配置）：

```
{% timeline 东爪哇省 玛琅县（视频 XX:XX） %}
印尼语：Provinsi Jawa Timur · Kabupaten Malang
英语：Province of East Java · Malang Regency
```

道路行：主行带 `label`，副行只写路名、缩进区分层级：

```
{% label 3 red %} 苏加诺-哈达路
  Jl. Soekarno Hatta
  Soekarno Hatta St.
```

**label 等级颜色映射**：NASIONAL → `red`、TOL → `green`、PROVINSI → `blue`。label 内编号显示纯编号（`3`、`024`），省码不进 label（盾牌色带概念）。

`gen_single_road_code` 按 region 分派：`cn` 走现有 G/S/X/省简称逻辑；`id` 走第 2 节等级判定（抽出共享函数，DRY）。

## 5. 配置、兼容性与测试

**配置新增**（`config/conf.example.yaml`，全部带默认值）：

```yaml
traffic_sign:
  color:
    blue: '#003E86'                  # 印尼 PROVINSI 色带
  indonesia_road_sign:
    template: asset/template/id_sheild.svg
    tol_keywords: ['收费', 'Tol']
    font:
      upper: asset/font/ClearviewHwy1W.ttf   # 色带小字
      upper_height: 45
      lower: asset/font/ClearviewHwy2W.ttf   # 大字编号
      lower_height: 135
video_info_layer:
  frame:
    area:      # 改为按行配置：{y, font_size}，[0]=主语言，[1:]=副语言
    road:      # 同上
```

**向后兼容**：`--region` 默认 `cn`，中国 CSV 全流程输出与现状完全一致（两行布局、现有坐标、现有 label）；印尼模式仅在新参数下激活。

**测试策略**（tests/ 现有 CLI 测试框架）：

1. 单测等级判定：`'3'`→NASIONAL、`'8'`+路名"收费"→TOL、`'023'`→PROVINSI、`'35-024'`→PROVINSI+省码 35、空→无盾牌、关键词边界（"Tol"大小写、中文"收费"）
2. 省码映射完整性：`Provinsi Jawa Timur → 35` 等 34 省全表
3. `generate_indonesia_shield`：输出 SVG 可解析、head 色带颜色正确（红/蓝）、色带文字含省码、大字为纯编号、字体与字号正确（1-W 45px / 2-W 135px）
4. 覆盖层：用真实印尼 CSV 生成样例图，断言三行文本、指南针避让取最大行宽
5. timeline：多语言逐行输出、印尼 label 颜色（red/green/blue）
6. 端到端冒烟：`--region id` 跑真实 CSV 一小段（如 100 帧）出图检查

**实施顺序**：`models`（枚举+类）→ `svg_gen`（盾牌生成器+居中排版）→ `create_pic`（解析分派+布局）→ `gen_road_info`（多语言）→ `config` + CLI → 测试。印尼语无需新字体（拉丁字母，覆盖层复用现有英文小字体；盾牌用 Clearview 系列）。
