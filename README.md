# gpxutil

目前存放自己处理 GPX 信息并自动生成相关文件的地方，待成体系之后编写自动化程序。

变动幅度会很大，请勿过分依赖该仓库。

## 功能

- `gpx2csv.py`：读取 GPX 文件，导出为 CSV 文件
- `svg_gen.py`：生成道路编号标志
- `create_pic.py`：根据修改后的 CSV 文件，生成信息图的每一帧

## `gpx2csv.py`

读取 GPX 文件的每个点，生成 CSV 文件，供修改后生成信息图。

需自行下载：

- [行政区划地图边界数据](https://map.vanbyte.com/street.html)。只能免费下载到县级。 需要的是压缩文件里面的 `./全国省市县边界GEOJson数据(不含乡镇街道)(边界数据未压缩)/map/city` 目录，解压后记下位置。
- [行政区划数据库](https://github.com/modood/Administrative-divisions-of-China)。需要的是 `./dist/data.sqlite`。解压后记下位置。

注意：区划边界数据并不精确，请自行参考实际情况编辑生成的 CSV 文件。

```python
import sqlite3
from gpx2csv import load_area_gdf_list, single_segment_gpx_file_path_to_csv

gdf_list = load_area_gdf_list('行政区划地图边界数据目录路径')
conn = sqlite3.connect('行政区划数据库文件路径')
single_segment_gpx_file_path_to_csv('GPX 文件路径', '生成的 CSV 文件路径', gdf_list, conn)
```

CSV 文件的列包括：

1. `index`：点的索引，以 `0` 开始
2. `time`：点的时间，格式为 `%Y-%m-%d %H:%M:%S`，时区为计算机时区
3. `elapsed_time`：已用时间，单位为秒（s）
4. `longitude`：经度，角度制，正数为东经
5. `latitude`：纬度，角度制，正数为北纬
6. `elevation`：海拔，单位为米（m）
7. `distance`：已行驶距离，单位为米（m）
8. `course`：方位角，角度制
9. `speed`：速度，单位为米每秒（m/s）
10. `province`：省级区划，包括“省”“市”“自治区”
11. `city`：地级区划，包括“市”“自治州”之类的后缀
12. `area`：县级区划，包括“区”“县”之类的后缀
13. `province_en`：省级区划的英文（目前需自行填写）
14. `city_en`：地级区划的英文（目前需自行填写）
15. `area_en`：县级区划的英文（目前需自行填写）
16. `road_num`：当前道路编号（需自行填写；省级高速需写为诸如 `晋S75` 的形式；如果有多个道路编号，则用 `,` 分割；其他情况参见 `svg_gen.py`）
17. `road_name`：当前道路名称（需自行填写）
18. `road_name_en`：当前道路名称的英文（需自行填写）



## `svg_gen.py`

生成道路编号标志。参考 [GB 5768.2-2022]((https://openstd.samr.gov.cn/bzgk/gb/newGbInfo?hcno=15B1FC09EE1AE92F1A9EC97BA3C9E451)) 标准。

暂不支持京津冀高速，且只做了汉语版本的。

```python
from svg_gen import generate_way_num_pad_to_file, generate_expwy_pad_to_file

# 国道、省道、县道、乡道等道路编号（交叉路口告知标志，路 5，参见图 210、图 E.171）
generate_way_num_pad_to_file('G221', './out/G221.svg')
# 高速公路编号（参见图 256、图 E.201)
generate_expwy_pad_to_file('./out/expwy_03.svg', 'G4511')   # 国家高速
generate_expwy_pad_to_file('./out/expwy_07.svg', 'S2', '豫') # 省级高速
# 高速公路编号（命名编号，路 36，参见图 257、图 E.202)
generate_expwy_pad_to_file('./out/expwy_04.svg', 'G5', name='测测高速') # 国家高速
generate_expwy_pad_to_file('./out/expwy_10.svg', 'S2', '豫', name='测试省级')    # 省级高速
```

需自行下载：[交通标志专用字体](https://xxgk.mot.gov.cn/2020/jigou/glj/202006/t20200623_3312662.html)。记下解压后各字体的路径，修改 `svg_gen.py` 中以下部分：

```python
FONT_TYPE_DIRECTORY_DICT = {
    'A': '/path/to/jtbz_A.ttf',
    'B': '/path/to/jtbz_B.ttf',
    'C': '/path/to/jtbz_C.ttf'
}
```

A 型字体的中文部分为华文黑体粗体，非免费商用，个人使用恐有版权纠纷。在本脚本场景下，A 型字体的使用场景只有高速公路的头部标志和底部路名，且这种情况下不会用到字母数字，故可以下载思源黑体的中文粗体代替：

```python
FONT_TYPE_DIRECTORY_DICT = {
    'A': '/path/to/SourceHanSansSC-Bold.ttf',
    'B': '/path/to/jtbz_B.ttf',
    'C': '/path/to/jtbz_C.ttf'
}
```

颜色为自己根据 [Roadgeek 字体](https://github.com/sammdot/roadgeek-fonts)里面提到的颜色定的，考虑了屏幕显示的问题。如果要改对应的颜色，可以修改以下部分：

```python
RED = '#B5273C'
WHITE = '#FFFFFF'
YELLOW = '#FFCD00'
BLACK = '#000000'
GREEN = '#006E55'
```

## `create_pic.py`

根据修改后的 CSV 文件，生成信息图的图像序列。理论上能够生成透明的视频文件，但实际发现 Premiere 无法处理这种文件，故目前还是生成图片序列，导入到 Premiere 内。

```python
from create_pic import generate_pic_from_csv

pic_list = generate_pic_from_csv('CSV 文件路径', start_index_after_fill=0, end_index_after_fill=-17, crop_start=1342, crop_end=1358)
```

参数含义：

1. `start_index`：输出帧的索引起始。对应 CSV 文件的 `index` 列。
2. `end_index`：输出帧的索引结束。对应 CSV 文件的 `index` 列。
3. `start_index_after_fill`：填补缺失帧之后的开始的序号（用于与视频对齐，填写秒数）
4. `end_index_after_fill`：填补缺失帧之后的结束的序号（用于与视频对齐，填写秒数）
5. `crop_start`：输出帧的序号起始，用于修改特定范围内的帧。对应 CSV 文件的 `index` 列。
6. `crop_end`：输出帧的序号结束，用于修改特定范围内的帧。对应 CSV 文件的 `index` 列。

运行前需参考[文档](https://cairosvg.org/documentation/#installation)解决 `Cairo` 依赖问题。

读取的 CSV 文件应为 UTF-8 带 BOM 编码（Excel 输出的 UTF-8 格式 CSV 是带 BOM 的）。

## `gen_road_info.py`

根据修改后的 CSV 文件，生成经由区域与道路的时间线。为方便自己写博客而编写。

```python
from gen_road_info import *

csv_dict_list = read_csv('CSV 文件路径')
city_info_list = get_info(csv_dict_list)
print(gen_route_info(city_info_list))
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