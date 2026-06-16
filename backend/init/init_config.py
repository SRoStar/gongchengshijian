"""
配置初始化模块
负责检测并初始化 config 文件夹和配置文件
"""

from pathlib import Path
import tomli


# ========== 可配置项默认值列表 ==========
# 格式: [(section, key, default_value), ...]
DEFAULT_CONFIG_ITEMS = [
    # 数据库配置
    ("database", "path", "db_table/"),
    # 服务器配置
    ("server", "host", "0.0.0.0"),
    ("server", "port", 8000),
    # 上传配置
    ("upload", "max_file_size", 10485760),
    ("upload", "allowed_extensions", [".cif", ".xyz", ".pdb", ".txt"]),
    # 安全配置
    ("security", "jwt_secret", "your-secret-key-change-in-production"),
    ("security", "token_expire_hours", 24),
    # Agent LLM 配置
    ("agent", "llm_model", "gpt-3.5-turbo"),
    ("agent", "llm_temperature", 0.7),
    ("agent", "llm_max_tokens", 1000),
    ("agent", "api_key", ""),
    ("agent", "base_url", ""),
    # RAG 配置
    ("rag", "top_k", 5),
    ("rag", "max_history", 10),
    ("rag", "chroma_path", "db_table/chroma_db"),
]


# 全局配置缓存
_config_cache = None


def get_config_path():
    """获取配置文件路径"""
    backend_dir = Path(__file__).resolve().parent.parent
    return backend_dir / "config" / "config.toml"


def load_config():
    """加载配置文件，返回配置字典"""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    config_file = get_config_path()
    if config_file.exists():
        with open(config_file, "rb") as f:
            _config_cache = tomli.load(f)
        return _config_cache
    return {}


def init_config():
    """
    检测并初始化配置文件夹
    - 如果 config 文件夹不存在，则创建
    - 如果 config 文件夹为空，则创建默认配置文件
    """
    global _config_cache

    # 获取 config 目录路径（相对于 backend 目录）
    backend_dir = Path(__file__).resolve().parent.parent
    config_dir = backend_dir / "config"
    config_file = config_dir / "config.toml"

    # 创建 config 目录（如果不存在）
    if not config_dir.exists():
        config_dir.mkdir(parents=True, exist_ok=True)
        print(f"[Config] 创建配置目录: {config_dir}")

    # 检查目录是否为空或配置文件不存在
    is_empty = not any(config_dir.iterdir()) if config_dir.exists() else True

    if is_empty or not config_file.exists():
        # 构建默认配置内容
        config_dict = {}
        for section, key, default_value in DEFAULT_CONFIG_ITEMS:
            if section not in config_dict:
                config_dict[section] = {}
            config_dict[section][key] = default_value

        # 生成 TOML 内容（带注释头部）
        header_lines = [
            "# 精准化学数据平台 - 配置文件",
            "#",
            "# 配置说明：",
            "# 1. 修改此文件后需重启服务器生效",
            "# 2. agent.api_key 为必填项，用于 AI 对话功能",
            "# 3. 生产环境请修改 security.jwt_secret",
            "#",
            "# 支持的 LLM 模型示例：",
            "#   - OpenAI: gpt-3.5-turbo, gpt-4, gpt-4-turbo",
            "#   - Claude: claude-3-opus, claude-3-sonnet, claude-3-haiku",
            "#   - 国内模型: qwen-turbo, qwen-plus, glm-4",
            "#",
            "# base_url 配置示例：",
            "#   - OpenAI 官方: https://api.openai.com/v1",
            "#   - Claude (Anthropic): https://api.anthropic.com",
            "#   - 阿里云通义: https://dashscope.aliyuncs.com/compatible-mode/v1",
            "#   - 智谱 AI: https://open.bigmodel.cn/api/paas/v4",
            "#",
            "",
        ]

        toml_lines = []
        for section, items in config_dict.items():
            toml_lines.append(f"[{section}]")
            for key, value in items.items():
                if isinstance(value, str):
                    toml_lines.append(f'{key} = "{value}"')
                elif isinstance(value, list):
                    list_str = ", ".join(f'"{v}"' for v in value)
                    toml_lines.append(f"{key} = [{list_str}]")
                else:
                    toml_lines.append(f"{key} = {value}")
            toml_lines.append("")

        # 写入配置文件（头部 + 配置内容）
        config_content = "\n".join(header_lines + toml_lines)
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(config_content)

        print(f"[Config] 创建默认配置文件: {config_file}")
        _config_cache = config_dict
        return True

    # 尝试读取现有配置
    try:
        with open(config_file, "rb") as f:
            _config_cache = tomli.load(f)
        print(f"[Config] 配置文件加载成功: {config_file}")
    except Exception as e:
        print(f"[Config] 警告: 配置文件格式错误 - {e}")

    return False

if __name__ == "__main__":
    init_config()