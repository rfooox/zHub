import yaml
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')

_config = None

def load_config():
    global _config
    if _config is None:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            _config = yaml.safe_load(f)
    return _config

def get_consul_config():
    config = load_config()
    return config.get('consul', {})

def is_consul_enabled():
    return get_consul_config().get('enabled', False)

def get_app_config():
    config = load_config()
    return config.get('app', {})

def get_health_check_config():
    config = load_config()
    return config.get('health_check', {})
