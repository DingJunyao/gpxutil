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
class TrafficSignConfig:
    color: ColorConfig
    font_path: FontPathConfig
    way_num_pad: WayNumPadConfig
    expwy_code_sign: ExpwyCodeSignConfig

@dataclass
class AreaInfoConfig:
    # gdf_dir_path: str
    # area_info_sqlite_path: str
    use: Literal['nominatim', 'gdf']
    nominatim: NominatimConfig = None
    gdf: GdfConfig = None

@dataclass
class VideoInfoLayerFontPathConfig:
    chinese: str
    english: str

@dataclass
class VideoInfoLayerImgPathConfig:
    compass: str
    route_time_sep: str

@dataclass
class VideoInfoLayerAreaConfig:
    chinese: PositionConfig
    english: PositionConfig

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
    chinese_y: int
    english_y: int

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