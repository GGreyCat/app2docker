# config.py
import os
import yaml

CONFIG_FILE = "config.yml"

def load_config():
    """加载或初始化配置文件"""
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "docker": {
                "registry": "docker.io",
                "registry_prefix": "",
                "default_push": False,
                "expose_port": 8080
            }
        }
        save_config(default_config)
        print(f"🆕 配置文件 {CONFIG_FILE} 不存在，已创建默认配置")
        return default_config

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"⚠️ 读取配置失败，使用默认配置: {e}")
        config = {}

    if 'docker' not in config:
        config['docker'] = {
            "registry": "docker.io",
            "registry_prefix": "",
            "default_push": False,
            "expose_port": 8080
        }
        save_config(config)

    return config

def save_config(config):
    """保存配置到文件"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)