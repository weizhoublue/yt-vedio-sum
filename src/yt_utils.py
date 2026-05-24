"""工具函数模块"""
import logging
import time
import functools
from typing import Callable, TypeVar, Any

T = TypeVar('T')


def retry(max_attempts: int = 3, delay: float = 2.0, backoff: float = 2.0):
    """重试装饰器，支持指数退避

    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 退避倍数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logging.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logging.error(f"All {max_attempts} attempts failed")
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry logic error: no exception was raised but retry exhausted")
        return wrapper
    return decorator


def setup_logging(level: str = "INFO", json_format: bool = False) -> None:
    """配置日志系统

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        json_format: 是否使用 JSON 格式
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    if json_format:
        # 简单 JSON 格式（生产环境使用结构化日志）
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                return f'{{"level": "{record.levelname}", "msg": "{record.getMessage()}", "time": "{self.formatTime(record)}"}}'
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


def check_dependencies() -> bool:
    """检查系统依赖是否完整

    Returns:
        True if all dependencies available
    """
    import shutil

    missing = []
    for cmd in ['ffmpeg', 'yt-dlp']:
        if not shutil.which(cmd):
            missing.append(cmd)

    if missing:
        logging.error(f"Missing system dependencies: {', '.join(missing)}")
        return False
    return True