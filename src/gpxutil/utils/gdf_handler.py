import os
import threading

import geopandas as gpd
from geopandas import GeoDataFrame
from loguru import logger
from tqdm import tqdm

from src.gpxutil.core.config import CONFIG_HANDLER
try:
    GEOJSON_DIR = CONFIG_HANDLER.config.area_info.gdf.gdf_dir_path
except Exception as e:
    logger.warning(e)

def load_area_gdf_list(geojson_dir: str) -> list[GeoDataFrame]:
    gdf_list = []
    filename_list = os.listdir(geojson_dir)
    for filename in tqdm(filename_list, total=len(filename_list), desc="Load Area GeoJSON files", unit='file(s)'):
        if filename.endswith(".json") or filename.endswith(".geojson"):
            gdf_list.append(gpd.read_file(os.path.join(geojson_dir, filename)))
    return gdf_list

class GDFListHandler:
    _instance_lock = threading.Lock()
    _instance = None  # 显式声明类变量用于存储单例实例
    _initialized = False  # 类变量用于跟踪是否已初始化

    def __init__(self, geojson_dir: str = None):
        # 通过类变量控制初始化逻辑，确保只执行一次
        if not GDFListHandler._initialized:
            if geojson_dir is not None:
                self.geojson_dir = geojson_dir
            else:
                if CONFIG_HANDLER.config.area_info.gdf is None:
                    logger.warning("GEOJSON_DIR is not set in config.yaml")
                    return
                else:
                    self.geojson_dir = GEOJSON_DIR
            self.list = self.load()
            GDFListHandler._initialized = True  # 标记为已初始化

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._instance_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def load(self):
        return load_area_gdf_list(self.geojson_dir)

if __name__ == '__main__':
    GDF_LIST_HANDLER = GDFListHandler()
    GDF_LIST_HANDLER_2 = GDFListHandler()
    print(GDF_LIST_HANDLER is GDF_LIST_HANDLER_2)  # 输出 True