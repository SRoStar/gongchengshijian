"""
初始化模块
包含配置初始化和数据库初始化功能
"""

from .init_config import init_config, load_config, get_config_path, DEFAULT_CONFIG_ITEMS

__all__ = [
    "init_config",
    "load_config",
    "get_config_path",
    "DEFAULT_CONFIG_ITEMS",
]