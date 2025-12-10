# gpxutil

目前存放自己处理 GPX 信息并自动生成相关文件的地方，待成体系之后编写自动化程序。

变动幅度会很大，请勿过分依赖该仓库。

## 功能

- 读取 GPX 文件，导出为 CSV 文件
- 生成道路编号标志
- 根据修改后的 CSV 文件，生成信息图的每一帧
- 根据修改后的 CSV 文件，生成经由区域与道路的时间线

## 准备工作

首先复制配置文件 `config/conf.full.yaml` 到：`config/conf.yaml`。

### 生成道路编号标志：依赖字体

需自行下载：[交通标志专用字体](https://xxgk.mot.gov.cn/2020/jigou/glj/202006/t20200623_3312662.html)。记下解压后各字体的路径，修改配置文件：

```yaml
traffic_sign:
  font_path:
    A: asset/font/jtbz_A.ttf
    B: asset/font/jtbz_B.ttf
    C: asset/font/jtbz_C.ttf
```

A 型字体的中文部分为华文黑体粗体，非免费商用，个人使用恐有版权纠纷。在本脚本场景下，A 型字体的使用场景只有高速公路的头部标志和底部路名，且这种情况下不会用到字母数字，故可以下载思源黑体的中文粗体代替：

```yaml
traffic_sign:
  font_path:
    A: asset/font/SourceHanSansSC-Bold.otf
    B: asset/font/jtbz_B.ttf
    C: asset/font/jtbz_C.ttf
```

### 生成信息图的图像序列：字体

记住字体路径，修改配置文件：

```yaml
video_info_layer:
  font_path:
    chinese: asset/font/SourceHanSans_static_super_otc.ttc
    chinese_index: 12
    english: asset/font/SourceSans3-Regular.otf
```

其中 `chinese_index` 表示中文字体的索引，如果没有这个概念，填 `0`。

### 生成信息图的图像序列：`Cairo`

参考[文档](https://cairosvg.org/documentation/#installation)解决 `Cairo` 依赖问题。

### 生成 CSV 文件：获取坐标行政区划和道路名称

注意：无论采用何种方式，区划边界、道路信息数据都可能不精确，请自行参考实际情况编辑生成的 CSV 文件。

本项目提供了四种方式，通过配置文件配置：

```yaml
area_info:
  use: nominatim
  nominatim:
    url: http://localhost:8080
  gdf:
    gdf_dir_path: asset/area_geojson
    area_info_sqlite_path: asset/area_code.sqlite
  baidu:
    ak: ...
    freq: 3
    get_en_result: true
  amap:
    ak: ...
    freq: 3
```

#### nominatim

数据源自 OpenStreetMap。部署麻烦，占用空间大（中国大陆的数据，下载解压处理后会占用 126 GB，初次部署要花费超过 20 小时）；但能够读取行政区划的英文（虽然只有县级的有行政级别名称），以及道路信息（虽然不稳定；一些道路能够读取英文）

参考的 Docker Compose 文件：

```yaml
version: '3'
services:
  nominatim:
    image: 'mediagis/nominatim:5.2'
    ports:
      - '8080:8080'
    volumes:
      - './ext/nominatim/data:/var/lib/postgresql/16/main'
      - './ext/nominatim/flatnode:/nominatim/flatnode'
    environment:
      PBF_URL: 'https://download.geofabrik.de/asia/china-latest.osm.pbf'
      REPLICATION_URL: 'https://download.geofabrik.de/asia/china-updates/'
      IMPORT_WIKIPEDIA: 'false'
      NOMINATIM_PASSWORD: very_secure_password
    container_name: nominatim
    shm_size: 1gb
```

本项目配置文件：

```yaml
area_info:
  use: nominatim
  nominatim:
    # nomination API 的开头，结尾不带斜杠
    url: http://localhost:8080
```

#### gdf

纯本地部署。只能够读取行政区划的中文信息，且只能精确到县级。不支持英文。

需自行下载：

- [行政区划地图边界数据](https://map.vanbyte.com/street.html)。只能免费下载到县级。 需要的是压缩文件里面的 `./全国省市县边界GEOJson数据(不含乡镇街道)(边界数据未压缩)/map/city` 目录，解压后记下位置。
- [行政区划数据库](https://github.com/modood/Administrative-divisions-of-China)。需要的是 `./dist/data.sqlite`。解压后记下位置。

```yaml
area_info:
  use: gdf
  gdf:
    gdf_dir_path: asset/area_geojson  # 行政区划地图边界数据
    area_info_sqlite_path: asset/area_code.sqlite # 行政区划数据库
```

#### 百度地图 API

配额小（个人开发者每日 300 次 API 调用，每秒一次点位记录只能处理五分钟的；且如果想要英文数据，要再次调用 API）

```yaml
area_info:
  use: baidu
  baidu:
    ak: 填写百度地图 API 的密钥
    # 频率限制，填写并发(次/秒)
    freq: 3
    # 是否获取英文名。如果获取，则一次执行两次 API 请求。能够获取到行政区划的英文名（不包括行政级别名称），道路则不一定能够取到
    get_en_result: true
```

#### 高德地图 API

配额比百度地图的多（个人开发者每月 150000 次 API 调用），但个人版不支持英文。

```yaml
area_info:
  use: amap
  amap:
    ak: 填写高德地图 API 的密钥
    # 频率限制，填写并发量上限(次/秒)
    freq: 3
```

## 用法

### 读取 GPX 文件，导出为 CSV 文件

```bash
python main.py transform "原 GPX 文件" ["坐标转换后的 GPX 文件"] ["CSV 文件"] [参数]
# 如
python main.py transform "E:\t\test.gpx" "E:\t\test_trans.gpx" "E:\t\test.csv"
```

参数：

- `--no_transform_coordinate`：不转换坐标
- `--coordinate_type`：坐标类型，可选 wgs84 或 gcj02
- `--transformed_coordinate_type`：转换后坐标类型，可选 wgs84 或 gcj02
- `--no_set_area`：不设置行政区划

默认从 WGS84 转换为 GCJ02。

CSV 文件格式为 UTF-8 带 BOM，列包括：

1. `index`：点的索引，以 `0` 开始
2. `time_date`：点的日期，格式为 `%Y/%m/%d`
3. `time_time`：点的时间，格式为 `%H:%M:%S`
4. `time_microsecond`: 点的微秒（us）
5. `elapsed_time`：已用时间，单位为秒（s）
6. `longitude`：经度，角度制，正数为东经
7. `latitude`：纬度，角度制，正数为北纬
8. `longitude_transformed`：转换后的经度，角度制，正数为东经
9. `latitude_transformed`：转换后的纬度，角度制，正数为北纬
10. `elevation`：海拔，单位为米（m）
11. `distance`：已行驶距离，单位为米（m）
12. `course`：方位角，角度制
13. `speed`：速度，单位为米每秒（m/s）
14. `province`：省级区划，包括“省”“市”“自治区”
15. `city`：地级区划，包括“市”“自治州”之类的后缀
16. `area`：县级区划，包括“区”“县”之类的后缀
17. `province_en`：省级区划的英文（目前需自行填写）
18. `city_en`：地级区划的英文（目前需自行填写）
19. `area_en`：县级区划的英文（目前需自行填写）
20. `road_num`：当前道路编号（需自行填写；省级高速需写为诸如 `晋S75` 的形式；如果有多个道路编号，则用 `,` 分割；其他情况参见 `svg_gen.py`）
21. `road_name`：当前道路名称（需自行填写）
22. `road_name_en`：当前道路名称的英文（需自行填写）
23. `memo`：备注（无实际用途）

### 生成道路编号标志

参考 [GB 5768.2-2022]((https://openstd.samr.gov.cn/bzgk/gb/newGbInfo?hcno=15B1FC09EE1AE92F1A9EC97BA3C9E451)) 标准。

暂不支持京津冀高速，且只做了汉语版本的。

输出 SVG 格式的文件。

```bash
python main.py pad 道路编号 [输出文件] [--name 道路名称]
# 如
python main.py pad G42
python main.py pad G42 --name 沪蓉高速
```

道路编号同时支持高速公路、国道、省道等。如果为省级高速，需填写为类似于 `苏S88` 的形式。

输出文件不填时，默认输出到工作目录下，名称为道路编号。

只有填写了道路名称，才会输出含道路名称的路牌。仅适用于高速公路。

颜色为自己根据 [Roadgeek 字体](https://github.com/sammdot/roadgeek-fonts)里面提到的颜色定的，考虑了屏幕显示的问题。如果要改对应的颜色，可以修改配置文件：

```yaml
traffic_sign:
  color:
    red: '#B5273C'
    white: '#FFFFFF'
    yellow: '#FFCD00'
    black: '#000000'
    green: '#006E55'
```

### 生成信息图的每一帧

根据修改后的 CSV 文件，生成信息图的图像序列。理论上能够生成透明的视频文件，但实际发现 Premiere 无法处理这种文件，故目前还是生成图片序列，导入到 Premiere 内。

```bash
python main.py overlay "原 CSV 文件" "输出目录" [参数]
# 如
python main.py overlay "E:\t\test.csv" "E:\t\overlay\"
```

参数含义：

1. `--start_index`：输出帧的索引起始。对应 CSV 文件的 `index` 列。
2. `--end_index`：输出帧的索引结束。对应 CSV 文件的 `index` 列。
3. `--start_index_after_fill`：填补缺失帧之后的开始的序号（用于与视频对齐，填写秒数）
4. `--end_index_after_fill`：填补缺失帧之后的结束的序号（用于与视频对齐，填写秒数）
5. `--crop_start`：输出帧的序号起始，用于修改特定范围内的帧。对应 CSV 文件的 `index` 列。
6. `--crop_end`：输出帧的序号结束，用于修改特定范围内的帧。对应 CSV 文件的 `index` 列。

读取的 CSV 文件应为 UTF-8 带 BOM 编码（因为经过修改后，很多情况下都存为这个编码的）。

### 根据修改后的 CSV 文件，生成经由区域与道路的时间线

根据修改后的 CSV 文件，生成经由区域与道路的时间线。为方便自己写博客而编写。

```bash
python main.py info "CSV 文件"
```

输出结果如下：

```text
{% timeline  江西省 九江市（视频 XX:XX） %}

<!-- timeline 浔阳区（视频 XX:XX） -->
滨江路 → 龙开河路 → 北径路 → 三马路 → {% label G351 red %} 浔阳西路 → 三马路 → 北径路 → 龙开河路 → 滨江路 → 滨江东路…
<!-- endtimeline -->
<!-- timeline 濂溪区（视频 XX:XX） -->
…滨江东路 → {% label S306 orange %} 滨江东路 → {% label S306 orange %} 九湖路 → {% label S306 orange %}  → {% label S306 orange %} 梅家洲渡口 → {% label S306 orange %}  → {% label S306 orange %} 九湖路 → {% label S306 orange %} 滨江东路 → 洪垅大道 → {% label X175 white %} 洪垅大道 → {% label S306 orange %} / {% label X175 white %} 九湖路 → 芳兰大道 → 九湖路 → {% label X175 white %} 九湖路 → {% label G351 red %} / {% label X175 white %} 九湖路…
<!-- endtimeline -->
<!-- timeline 浔阳区（视频 XX:XX） -->
…{% label G351 red %} / {% label X175 white %} 九湖路…
<!-- endtimeline -->
<!-- timeline 濂溪区（视频 XX:XX） -->
…{% label G351 red %} / {% label X175 white %} 九湖路 → 琴湖大道 → 琴湖大道互通 → 昌九快速路 → 九江东收费站 → 赣 {% label S22 green %} 都九高速…
<!-- endtimeline -->
<!-- timeline 湖口县（视频 XX:XX） -->
…赣 {% label S22 green %} 都九高速 → 石钟山服务区 → 赣 {% label S22 green %} 都九高速…
<!-- endtimeline -->
<!-- timeline 都昌县（视频 XX:XX） -->
…赣 {% label S22 green %} 都九高速 → {% label G56 green %} / 赣 {% label S22 green %} 杭瑞高速 → {% label G56 green %} 杭瑞高速…
<!-- endtimeline -->
{% endtimeline %}
{% timeline  江西省 上饶市（视频 XX:XX） %}

<!-- timeline 鄱阳县（视频 XX:XX） -->
…{% label G56 green %} 杭瑞高速…
<!-- endtimeline -->
{% endtimeline %}
{% timeline  江西省 景德镇市（视频 XX:XX） %}

<!-- timeline 浮梁县（视频 XX:XX） -->
…{% label G56 green %} 杭瑞高速 → 景德镇西互通（景德镇西收费站） → 迎宾大道…
<!-- endtimeline -->
<!-- timeline 昌江区（视频 XX:XX） -->
…迎宾大道 → {% label G351 red %} 迎宾大道 → 新平路 → 珠山大道 → {% label S308 orange %} 珠山大道…
<!-- endtimeline -->
<!-- timeline 珠山区（视频 XX:XX） -->
…{% label S308 orange %} 珠山大道 → 中华南路 → 麻石上弄 → 中山南路 → 麻石上弄 → 中华南路 → {% label S308 orange %} 珠山大道 → 莲社南路
<!-- endtimeline -->
{% endtimeline %}
```