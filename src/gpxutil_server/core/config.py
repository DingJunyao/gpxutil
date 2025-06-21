import threading
import yaml

from src.gpxutil_server.models.config import *


CONFIG_FILE_PATH = 'config/server.yaml'

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
        mongodb = MongoDbConfig(
            host=config_raw['mongodb']['host'],
            port=config_raw['mongodb']['port'] if 'port' in config_raw['mongodb'] else 27017,
            username=config_raw['mongodb']['username'],
            password=config_raw['mongodb']['password'],
            db=config_raw['mongodb']['db']
        )
        redis = RedisConfig(
            host=config_raw['redis']['host'],
            port=config_raw['redis']['port'] if 'port' in config_raw['redis'] else 6379,
            password=config_raw['redis']['password'],
            db=config_raw['redis']['db']
        )
        return Config(
            mongodb=mongodb,
            redis=redis
        )

CONFIG_HANDLER = ConfigHandler()

if __name__ == '__main__':
    config_handler = ConfigHandler()
    print(config_handler.config.mongodb.host)