import threading
import yaml

from src.gpxutil.models.config import *


CONFIG_FILE_PATH = 'config/conf.yaml'

class ConfigHandler:
    _instance_lock = threading.Lock()
    _instance = None  # 显式声明类变量用于存储单例实例
    _initialized = False  # 类变量用于跟踪是否已初始化

    def __init__(self, config_path: str = None):
        if not ConfigHandler._initialized:
            if config_path is not None:
                self.config_path = config_path
            else:
                self.config_path = CONFIG_FILE_PATH
            self.config = self.load()
            ConfigHandler._initialized = True  # 标记为已初始化

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._instance_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def load(self):
        with open(self.config_path, 'r', encoding='utf-8') as config_file:
            config_raw = yaml.safe_load(config_file)
        config = self.parse_config(config_raw)
        return config

    @staticmethod
    def parse_config(config_raw):
        match config_raw['area_info']['use']:
            case 'nominatim':
                nominatim = NominatimConfig(
                    url=config_raw['area_info']['nominatim']['url']
                )
                area_info = AreaInfoConfig(
                    use='nominatim',
                    nominatim=nominatim
                )
            case 'gdf':
                gdf = GdfConfig(
                    gdf_dir_path=config_raw['area_info']['gdf']['gdf_dir_path'],
                    area_info_sqlite_path=config_raw['area_info']['gdf']['area_info_sqlite_path']
                )
                area_info = AreaInfoConfig(
                    use='gdf',
                    gdf=gdf
                )
            case 'baidu':
                baidu = BaiduConfig(
                    ak=config_raw['area_info']['baidu']['ak'],
                    freq=config_raw['area_info']['baidu']['freq'],
                    get_en_result=config_raw['area_info']['baidu']['get_en_result']
                )
                area_info = AreaInfoConfig(
                    use='baidu',
                    baidu=baidu
                )
            case 'amap':
                amap = AmapConfig(
                    ak=config_raw['area_info']['amap']['ak'],
                    freq=config_raw['area_info']['amap']['freq']
                )
                area_info = AreaInfoConfig(
                    use='amap',
                    amap=amap
                )
            case _:
                raise ValueError('area_info.use in config is invalid')
        # if config_raw['area_info']['use'] == 'nominatim':
        #     nominatim = NominatimConfig(
        #         url=config_raw['area_info']['nominatim']['url']
        #     )
        #     area_info = AreaInfoConfig(
        #         use='nominatim',
        #         nominatim=nominatim
        #     )
        # else:
        #     gdf = GdfConfig(
        #         gdf_dir_path=config_raw['area_info']['gdf_dir_path'],
        #         area_info_sqlite_path=config_raw['area_info']['area_info_sqlite_path']
        #     )
        #     area_info = AreaInfoConfig(
        #         use='gdf',
        #         gdf=gdf
        #     )

        color = ColorConfig(
            red=config_raw['traffic_sign']['color']['red'],
            white=config_raw['traffic_sign']['color']['white'],
            yellow=config_raw['traffic_sign']['color']['yellow'],
            black=config_raw['traffic_sign']['color']['black'],
            green=config_raw['traffic_sign']['color']['green']
        )

        font_path = FontPathConfig(
            A=config_raw['traffic_sign']['font_path']['A'],
            B=config_raw['traffic_sign']['font_path']['B'],
            C=config_raw['traffic_sign']['font_path']['C']
        )

        # word = BoxConfig(
        #     x=config_raw['traffic_sign']['way_num_pad']['word']['x'],
        #     y=config_raw['traffic_sign']['way_num_pad']['word']['y'],
        #     width=config_raw['traffic_sign']['way_num_pad']['word']['width'],
        #     height=config_raw['traffic_sign']['way_num_pad']['word']['height']
        # )

        # way_num_pad_color_background = WayNumPadColorSingleConfig(
        #     national=config_raw['traffic_sign']['way_num_pad']['color']['background']['national'],
        #     province=config_raw['traffic_sign']['way_num_pad']['color']['background']['province'],
        #     other=config_raw['traffic_sign']['way_num_pad']['color']['background']['other']
        # )

        # way_num_pad_color_stroke = WayNumPadColorSingleConfig(
        #     national=config_raw['traffic_sign']['way_num_pad']['color']['stroke']['national'],
        #     province=config_raw['traffic_sign']['way_num_pad']['color']['stroke']['province'],
        #     other=config_raw['traffic_sign']['way_num_pad']['color']['stroke']['other']
        # )

        # way_num_pad_color = WayNumPadColorConfig(
        #     background=way_num_pad_color_background,
        #     stroke=way_num_pad_color_stroke
        # )

        way_num_pad = WayNumPadConfig(
            template_path=config_raw['traffic_sign']['way_num_pad']['template_path'],
            # width=config_raw['traffic_sign']['way_num_pad']['width'],
            # height=config_raw['traffic_sign']['way_num_pad']['height'],
            # word=word,
            # color=way_num_pad_color
        )

        # expwy_code_sign_color_banner = ExpwyCodeSignBannerBackgroundColorConfig(
        #     national=config_raw['traffic_sign']['expwy_code_sign']['color']['background']['banner']['national'],
        #     province=config_raw['traffic_sign']['expwy_code_sign']['color']['background']['banner']['province']
        # )

        # expwy_code_sign_color = ExpwyCodeSignColorConfig(
        #     banner=expwy_code_sign_color_banner,
        #     main=config_raw['traffic_sign']['expwy_code_sign']['color']['background']['main']
        # )

        # expwy_code_sign_without_name_num1_banner_text = ExpwyCodeSignBannerTextConfig(
        #     national=BoxConfig(
        #         x=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_1']['banner_text']['national'][
        #             'x'],
        #         y=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_1']['banner_text']['national'][
        #             'y'],
        #         width=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_1']['banner_text']['national'][
        #             'width'],
        #         height=
        #         config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_1']['banner_text']['national'][
        #             'height']
        #     ),
        #     province=BoxConfig(
        #         x=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_1']['banner_text']['province'][
        #             'x'],
        #         y=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_1']['banner_text']['province'][
        #             'y'],
        #         width=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_1']['banner_text']['province'][
        #             'width'],
        #         height=
        #         config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_1']['banner_text']['province'][
        #             'height']
        #     )
        # )

        expwy_code_sign_without_name_num1 = ExpwyCodeSignWithoutNameNum1And2Config(
            template_path=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_1']['template_path'],
            # code=BoxConfig(
            #     x=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_1']['code']['x'],
            #     y=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_1']['code']['y'],
            #     width=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_1']['code']['width'],
            #     height=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_1']['code']['height']
            # ),
            # banner_text=expwy_code_sign_without_name_num1_banner_text
        )

        expwy_code_sign_without_name_num2 = ExpwyCodeSignWithoutNameNum1And2Config(
            template_path=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_2']['template_path'],
            # code=BoxConfig(
            #     x=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_2']['code']['x'],
            #     y=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_2']['code']['y'],
            #     width=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_2']['code']['width'],
            #     height=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_2']['code']['height']
            # ),
            # banner_text=expwy_code_sign_without_name_num1_banner_text
        )

        # expwy_code_sign_without_name_num4_code = ExpwyCodeSignNum4CodeConfig(
        #     big=BoxConfig(
        #         x=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_4']['code']['big']['x'],
        #         y=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_4']['code']['big']['y'],
        #         width=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_4']['code']['big']['width'],
        #         height=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_4']['code']['big']['height']
        #     ),
        #     small=BoxConfig(
        #         x=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_4']['code']['small']['x'],
        #         y=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_4']['code']['small']['y'],
        #         width=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_4']['code']['small']['width'],
        #         height=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_4']['code']['small']['height']
        #     )
        # )

        expwy_code_sign_without_name_num4 = ExpwyCodeSignWithoutNameNum4Config(
            template_path=config_raw['traffic_sign']['expwy_code_sign']['without_name']['num_4']['template_path'],
            # code=expwy_code_sign_without_name_num4_code,
            # banner_text=expwy_code_sign_without_name_num1_banner_text
        )

        expwy_code_sign_without_name = ExpwyCodeSignWithoutNameConfig(
            num_1=expwy_code_sign_without_name_num1,
            num_2=expwy_code_sign_without_name_num2,
            num_4=expwy_code_sign_without_name_num4
        )

        # expwy_code_sign_with_name_num1_banner_text = ExpwyCodeSignBannerTextConfig(
        #     national=BoxConfig(
        #         x=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_1']['banner_text']['national']['x'],
        #         y=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_1']['banner_text']['national']['y'],
        #         width=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_1']['banner_text']['national'][
        #             'width'],
        #         height=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_1']['banner_text']['national'][
        #             'height']
        #     ),
        #     province=BoxConfig(
        #         x=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_1']['banner_text']['province']['x'],
        #         y=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_1']['banner_text']['province']['y'],
        #         width=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_1']['banner_text']['province'][
        #             'width'],
        #         height=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_1']['banner_text']['province'][
        #             'height']
        #     )
        # )

        expwy_code_sign_with_name_num1 = ExpwyCodeSignWithNameNum1And2Config(
            template_path=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_1']['template_path'],
            # code=BoxConfig(
            #     x=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_1']['code']['x'],
            #     y=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_1']['code']['y'],
            #     width=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_1']['code']['width'],
            #     height=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_1']['code']['height']
            # ),
            # name=BoxConfig(
            #     x=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_1']['name']['x'],
            #     y=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_1']['name']['y'],
            #     width=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_1']['name']['width'],
            #     height=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_1']['name']['height']
            # ),
            # banner_text=expwy_code_sign_with_name_num1_banner_text
        )

        expwy_code_sign_with_name_num2 = ExpwyCodeSignWithNameNum1And2Config(
            template_path=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_2']['template_path'],
            # code=BoxConfig(
            #     x=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_2']['code']['x'],
            #     y=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_2']['code']['y'],
            #     width=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_2']['code']['width'],
            #     height=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_2']['code']['height']
            # ),
            # name=BoxConfig(
            #     x=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_2']['name']['x'],
            #     y=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_2']['name']['y'],
            #     width=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_2']['name']['width'],
            #     height=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_2']['name']['height']
            # ),
            # banner_text=expwy_code_sign_with_name_num1_banner_text
        )

        # expwy_code_sign_with_name_num4_code = ExpwyCodeSignNum4CodeConfig(
        #     big=BoxConfig(
        #         x=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_4']['code']['big']['x'],
        #         y=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_4']['code']['big']['y'],
        #         width=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_4']['code']['big']['width'],
        #         height=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_4']['code']['big']['height']
        #     ),
        #     small=BoxConfig(
        #         x=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_4']['code']['small']['x'],
        #         y=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_4']['code']['small']['y'],
        #         width=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_4']['code']['small']['width'],
        #         height=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_4']['code']['small']['height']
        #     )
        # )

        expwy_code_sign_with_name_num4 = ExpwyCodeSignWithNameNum4Config(
            template_path=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_4']['template_path'],
            # code=expwy_code_sign_with_name_num4_code,
            # name=BoxConfig(
            #     x=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_4']['name']['x'],
            #     y=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_4']['name']['y'],
            #     width=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_4']['name']['width'],
            #     height=config_raw['traffic_sign']['expwy_code_sign']['with_name']['num_4']['name']['height']
            # ),
            # banner_text=expwy_code_sign_with_name_num1_banner_text
        )

        expwy_code_sign_with_name = ExpwyCodeSignWithNameConfig(
            num_1=expwy_code_sign_with_name_num1,
            num_2=expwy_code_sign_with_name_num2,
            num_4=expwy_code_sign_with_name_num4
        )

        expwy_code_sign = ExpwyCodeSignConfig(
            # color=expwy_code_sign_color,
            without_name=expwy_code_sign_without_name,
            with_name=expwy_code_sign_with_name
        )

        traffic_sign = TrafficSignConfig(
            color=color,
            font_path=font_path,
            way_num_pad=way_num_pad,
            expwy_code_sign=expwy_code_sign
        )

        video_info_layer_font_path = VideoInfoLayerFontPathConfig(
            chinese=config_raw['video_info_layer']['font_path']['chinese'],
            english=config_raw['video_info_layer']['font_path']['english']
        )

        video_info_layer_img_path = VideoInfoLayerImgPathConfig(
            compass=config_raw['video_info_layer']['img_path']['compass'],
            route_time_sep=config_raw['video_info_layer']['img_path']['route_time_sep']
        )

        video_info_layer_area = VideoInfoLayerAreaConfig(
            chinese=PositionConfig(
                x=config_raw['video_info_layer']['frame']['area']['chinese']['x'],
                y=config_raw['video_info_layer']['frame']['area']['chinese']['y']
            ),
            english=PositionConfig(
                x=config_raw['video_info_layer']['frame']['area']['english']['x'],
                y=config_raw['video_info_layer']['frame']['area']['english']['y']
            )
        )

        video_info_layer_road_sign = VideoInfoLayerRoadSignConfig(
            width=config_raw['video_info_layer']['frame']['road']['sign']['width'],
            height=config_raw['video_info_layer']['frame']['road']['sign']['height'],
            space=config_raw['video_info_layer']['frame']['road']['sign']['space'],
            char_space=config_raw['video_info_layer']['frame']['road']['sign']['char_space']
        )

        video_info_layer_road = VideoInfoLayerRoadConfig(
            x=config_raw['video_info_layer']['frame']['road']['x'],
            middle_y=config_raw['video_info_layer']['frame']['road']['middle_y'],
            sign=video_info_layer_road_sign,
            chinese_y=config_raw['video_info_layer']['frame']['road']['chinese_y'],
            english_y=config_raw['video_info_layer']['frame']['road']['english_y']
        )

        video_info_layer_compass = PositionConfig(
            x=config_raw['video_info_layer']['frame']['compass']['x'],
            y=config_raw['video_info_layer']['frame']['compass']['y']
        )

        video_info_layer_route_time_used = VideoInfoLayerRouteTimeUsedConfig(
            route=PositionRightTopConfig(
                right_x=config_raw['video_info_layer']['frame']['route_time']['used']['route']['right_x'],
                y=config_raw['video_info_layer']['frame']['route_time']['used']['route']['y']
            ),
            time=PositionRightTopConfig(
                right_x=config_raw['video_info_layer']['frame']['route_time']['used']['time']['right_x'],
                y=config_raw['video_info_layer']['frame']['route_time']['used']['time']['y']
            )
        )

        video_info_layer_route_time_sep = PositionConfig(
            x=config_raw['video_info_layer']['frame']['route_time']['sep']['x'],
            y=config_raw['video_info_layer']['frame']['route_time']['sep']['y']
        )

        video_info_layer_route_time_remain = VideoInfoLayerRouteTimeRemainConfig(
            route=PositionConfig(
                x=config_raw['video_info_layer']['frame']['route_time']['remain']['route']['x'],
                y=config_raw['video_info_layer']['frame']['route_time']['remain']['route']['y']
            ),
            time=PositionConfig(
                x=config_raw['video_info_layer']['frame']['route_time']['remain']['time']['x'],
                y=config_raw['video_info_layer']['frame']['route_time']['remain']['time']['y']
            )
        )

        video_info_layer_route_time = VideoInfoLayerRouteTimeConfig(
            used=video_info_layer_route_time_used,
            sep=video_info_layer_route_time_sep,
            remain=video_info_layer_route_time_remain
        )

        video_info_layer_altitude_num = PositionRightTopConfig(
            right_x=config_raw['video_info_layer']['frame']['altitude']['num']['right_x'],
            y=config_raw['video_info_layer']['frame']['altitude']['num']['y']
        )

        video_info_layer_altitude_unit = PositionRightTopConfig(
            right_x=config_raw['video_info_layer']['frame']['altitude']['unit']['right_x'],
            y=config_raw['video_info_layer']['frame']['altitude']['unit']['y']
        )

        video_info_layer_altitude = VideoInfoLayerAltitudeConfig(
            num=video_info_layer_altitude_num,
            unit=video_info_layer_altitude_unit
        )

        video_info_layer_speed_num = PositionRightTopConfig(
            right_x=config_raw['video_info_layer']['frame']['speed']['num']['right_x'],
            y=config_raw['video_info_layer']['frame']['speed']['num']['y']
        )

        video_info_layer_speed_unit = PositionRightTopConfig(
            right_x=config_raw['video_info_layer']['frame']['speed']['unit']['right_x'],
            y=config_raw['video_info_layer']['frame']['speed']['unit']['y']
        )

        video_info_layer_speed = VideoInfoLayerSpeedConfig(
            num=video_info_layer_speed_num,
            unit=video_info_layer_speed_unit
        )

        video_info_layer_frame = VideoInfoLayerFrameConfig(
            width=config_raw['video_info_layer']['frame']['width'],
            height=config_raw['video_info_layer']['frame']['height'],
            dpi=config_raw['video_info_layer']['frame']['dpi'],
            min_space =  config_raw['video_info_layer']['frame']['min_space'],
            area=video_info_layer_area,
            road=video_info_layer_road,
            compass=video_info_layer_compass,
            route_time=video_info_layer_route_time,
            altitude=video_info_layer_altitude,
            speed=video_info_layer_speed
        )
        video_info_layer = VideoInfoLayerConfig(
            font_path=video_info_layer_font_path,
            img_path=video_info_layer_img_path,
            frame=video_info_layer_frame
        )
        return Config(
            area_info=area_info,
            traffic_sign=traffic_sign,
            video_info_layer=video_info_layer
        )

CONFIG_HANDLER = ConfigHandler()

if __name__ == '__main__':
    config_handler = ConfigHandler()
    print(config_handler.config.traffic_sign.color)