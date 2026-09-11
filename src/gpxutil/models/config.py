from dataclasses import dataclass, field
from typing import Dict, List, Union, Literal


@dataclass
class NominatimConfig:
    """Nominatim API 配置"""
    url: str

@dataclass
class GdfConfig:
    gdf_dir_path: str
    area_info_sqlite_path: str

@dataclass
class BaiduConfig:
    ak: str
    freq: int
    get_en_result: bool

@dataclass
class AmapConfig:
    ak: str
    freq: int

@dataclass
class PositionConfig:
    """记录左上角位置"""
    x: float
    y: float

@dataclass
class PositionRightTopConfig:
    """记录右上角位置"""
    right_x: float
    y: float

# @dataclass
# class SizeConfig:
#     """记录宽高"""
#     width: float
#     height: float

# class BoxConfig(PositionConfig, SizeConfig):
#     """Position and size of a box (e.g. Picture, Text)"""
#     def __init__(self, x: float, y: float, width: float, height: float):
#         self.x = x
#         self.y = y
#         self.width = width
#         self.height = height

@dataclass
class ColorConfig:
    red: str
    white: str
    yellow: str
    black: str
    green: str
    blue: str

@dataclass
class FontPathConfig:
    A: str
    B: str
    C: str

# @dataclass
# class WayNumPadColorSingleConfig:
#     national: str
#     province: str
#     other: str

# @dataclass
# class WayNumPadColorConfig:
#     background: WayNumPadColorSingleConfig
#     stroke: WayNumPadColorSingleConfig

@dataclass
class WayNumPadConfig:
    template_path: str
    # width: int
    # height: int
    # word: BoxConfig
    # color: WayNumPadColorConfig

# @dataclass
# class ExpwyCodeSignBannerBackgroundColorConfig:
#     national: str
#     province: str

# @dataclass
# class ExpwyCodeSignColorConfig:
#     banner: ExpwyCodeSignBannerBackgroundColorConfig
#     main: str

# @dataclass
# class ExpwyCodeSignBannerTextConfig:
#     national: BoxConfig
#     province: BoxConfig

# @dataclass
# class ExpwyCodeSignNum4CodeConfig:
#     big: BoxConfig
#     small: BoxConfig

@dataclass
class ExpwyCodeSignWithoutNameNum1And2Config:
    template_path: str
    # code: BoxConfig
    # banner_text: ExpwyCodeSignBannerTextConfig

@dataclass
class ExpwyCodeSignWithoutNameNum4Config:
    template_path: str
    # code: ExpwyCodeSignNum4CodeConfig
    # banner_text: ExpwyCodeSignBannerTextConfig

@dataclass
class ExpwyCodeSignWithoutNameConfig:
    num_1: ExpwyCodeSignWithoutNameNum1And2Config
    num_2: ExpwyCodeSignWithoutNameNum1And2Config
    num_4: ExpwyCodeSignWithoutNameNum4Config

@dataclass
class ExpwyCodeSignWithNameNum1And2Config:
    template_path: str
    # code: BoxConfig
    # name: BoxConfig
    # banner_text: ExpwyCodeSignBannerTextConfig

@dataclass
class ExpwyCodeSignWithNameNum4Config:
    template_path: str
    # code: ExpwyCodeSignNum4CodeConfig
    # name: BoxConfig
    # banner_text: ExpwyCodeSignBannerTextConfig

@dataclass
class ExpwyCodeSignWithNameConfig:
    num_1: ExpwyCodeSignWithNameNum1And2Config
    num_2: ExpwyCodeSignWithNameNum1And2Config
    num_4: ExpwyCodeSignWithNameNum4Config

@dataclass
class ExpwyCodeSignConfig:
    # color: ExpwyCodeSignColorConfig
    without_name: ExpwyCodeSignWithoutNameConfig
    with_name: ExpwyCodeSignWithNameConfig

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
class AreaInfoConfig:
    # gdf_dir_path: str
    # area_info_sqlite_path: str
    use: Literal['nominatim', 'gdf', 'baidu', 'amap']
    nominatim: NominatimConfig = None
    gdf: GdfConfig = None
    baidu: BaiduConfig = None
    amap: AmapConfig = None

@dataclass
class VideoInfoLayerFontPathConfig:
    chinese: str
    english: str
    chinese_index: int = 0
    # 副语言斜体字体（印尼语行专用），未配置时回退 english 正体
    english_italic: str | None = None

@dataclass
class VideoInfoLayerImgPathConfig:
    compass: str
    route_time_sep: str

@dataclass
class VideoInfoLayerTextLineConfig:
    """覆盖层一行文本的横坐标与字号。

    纵坐标不在此配置：由 bottom_y 锚定最后一行、按各行实际渲染高度自下而上堆叠计算
    （行数增减时上方行自然上下移动，最后一行位置恒定）。
    """
    font_size: int = 64
    # 区域行由配置直接给出 x；道路行不单独提供 x，绘制时沿用道路整体 x
    x: float | None = None

@dataclass
class VideoInfoLayerAreaConfig:
    lines: list[VideoInfoLayerTextLineConfig]
    bottom_y: float   # 最后一行文本的顶部 y
    line_gap: float   # 相邻行的视觉空隙

@dataclass
class VideoInfoLayerRoadSignConfig:
    width: int
    height: int
    space: int
    char_space: int

@dataclass
class VideoInfoLayerRoadConfig:
    x: int
    middle_y: int
    sign: VideoInfoLayerRoadSignConfig
    lines: list[VideoInfoLayerTextLineConfig]  # 只含 font_size，x 用上面的 x
    bottom_y: float
    line_gap: float

@dataclass
class VideoInfoLayerRouteTimeUsedConfig:
    route: PositionRightTopConfig
    time: PositionRightTopConfig

@dataclass
class VideoInfoLayerRouteTimeRemainConfig:
    route: PositionConfig
    time: PositionConfig

@dataclass
class VideoInfoLayerRouteTimeConfig:
    used: VideoInfoLayerRouteTimeUsedConfig
    sep: PositionConfig
    remain: VideoInfoLayerRouteTimeRemainConfig

@dataclass
class VideoInfoLayerAltitudeConfig:
    num: PositionRightTopConfig
    unit: PositionRightTopConfig

@dataclass
class VideoInfoLayerSpeedConfig:
    num: PositionRightTopConfig
    unit: PositionRightTopConfig

@dataclass
class VideoInfoLayerFrameConfig:
    width: int
    height: int
    dpi: int
    min_space: int
    area: VideoInfoLayerAreaConfig
    road: VideoInfoLayerRoadConfig
    compass: PositionConfig
    route_time: VideoInfoLayerRouteTimeConfig
    altitude: VideoInfoLayerAltitudeConfig
    speed: VideoInfoLayerSpeedConfig

@dataclass
class VideoInfoLayerConfig:
    font_path: VideoInfoLayerFontPathConfig
    img_path: VideoInfoLayerImgPathConfig
    frame: VideoInfoLayerFrameConfig

@dataclass
class Config:
    area_info: AreaInfoConfig
    traffic_sign: TrafficSignConfig
    video_info_layer: VideoInfoLayerConfig


if __name__ == '__main__':
    # BoxConfig(1,2,3,4)
    pass