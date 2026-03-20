import yaml
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')

_config = None

def load_config():
    global _config
    if _config is None:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            _config = yaml.safe_load(f)
        
        _config['consul']['enabled'] = os.getenv('CONSUL_ENABLED', 'true').lower() == 'true'
        _config['consul']['host'] = os.getenv('CONSUL_HOST', _config['consul'].get('host', '127.0.0.1'))
        _config['consul']['port'] = int(os.getenv('CONSUL_PORT', _config['consul'].get('port', 8500)))
        _config['consul']['datacenter'] = os.getenv('CONSUL_DATACENTER', _config['consul'].get('datacenter', 'dc1'))
        _config['consul']['scheme'] = os.getenv('CONSUL_SCHEME', _config['consul'].get('scheme', 'http'))
        
        _config['app']['host'] = os.getenv('APP_HOST', _config['app'].get('host', '0.0.0.0'))
        _config['app']['port'] = int(os.getenv('APP_PORT', _config['app'].get('port', 5000)))
        
        health_enabled = os.getenv('HEALTH_CHECK_ENABLED', 'true').lower() == 'true'
        _config['health_check']['enabled'] = health_enabled
        _config['health_check']['interval'] = int(os.getenv('HEALTH_CHECK_INTERVAL', _config['health_check'].get('interval', 60)))
        _config['health_check']['timeout'] = int(os.getenv('HEALTH_CHECK_TIMEOUT', _config['health_check'].get('timeout', 5)))
        
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
