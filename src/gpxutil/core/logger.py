from loguru import logger
from pathlib import Path

# 统一日志路径（示例：项目根目录下的 logs 文件夹）
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)  # 自动创建日志目录
LOG_PATH = LOG_DIR / "app.log"

# 添加全局文件日志配置
logger.add(
    LOG_PATH,
    rotation="10 MB",          # 日志分片：每10MB压缩分割
    retention="30 days",       # 保留时长：30天
    enqueue=True,               # 多进程安全
    encoding="utf-8",
)

"""
2.在项目入口初始化配置（如 main.py）：

from core.logger import logger

if __name__ == "__main__":
    logger.info("程序启动")  # 测试日志输出
    
3. 其他模块直接引用（如 module_a.py）：

python
from loguru import logger  # 直接使用全局单例

def demo():
    logger.debug("模块A的日志")
"""