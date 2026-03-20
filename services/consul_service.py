import requests
from services.config_service import get_consul_config

class ConsulService:

    def __init__(self):
        self.config = get_consul_config()
        self.host = self.config.get('host', '127.0.0.1')
        self.port = self.config.get('port', 8500)
        self.datacenter = self.config.get('datacenter', 'dc1')
        self.scheme = self.config.get('scheme', 'http')

    @property
    def base_url(self):
        return f'{self.scheme}://{self.host}:{self.port}'

    def is_available(self):
        try:
            response = requests.get(f'{self.base_url}/v1/status/leader', timeout=3)
            return response.status_code == 200
        except Exception:
            return False

    def get_services(self):
        try:
            response = requests.get(f'{self.base_url}/v1/catalog/services', timeout=5)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception:
            return {}

    def get_service_instances(self, service_name):
        try:
            params = {'dc': self.datacenter}
            response = requests.get(f'{self.base_url}/v1/health/service/{service_name}', params=params, timeout=5)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception:
            return []

    def get_service_health(self, service_name):
        instances = self.get_service_instances(service_name)
        health_info = []
        for instance in instances:
            checks = instance.get('Checks', [])
            status = 'passing'
            for check in checks:
                if check.get('Status') == 'critical':
                    status = 'critical'
                    break
                elif check.get('Status') == 'warning':
                    status = 'warning'
            health_info.append({
                'node': instance.get('Node', {}).get('Node', ''),
                'address': instance.get('Service', {}).get('Address', ''),
                'port': instance.get('Service', {}).get('Port', 0),
                'service_name': instance.get('Service', {}).get('ServiceName', ''),
                'status': status
            })
        return health_info

    def register_service(self, name, url, port=None, tags=None, meta=None, check_type='http', interval='30s'):
        try:
            if port is None:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                port = parsed.port or (443 if parsed.scheme == 'https' else 80)
                address = parsed.hostname or url
            else:
                address = url
            tags = tags or []
            meta = meta or {}
            if check_type == 'http':
                check = {
                    'Name': f'{name}-health',
                    'HTTP': url if url.startswith('http') else f'http://{url}',
                    'Interval': interval,
                    'Timeout': '5s'
                }
            else:
                check = {
                    'Name': f'{name}-health',
                    'TCP': f'{address}:{port}',
                    'Interval': interval,
                    'Timeout': '5s'
                }
            payload = {
                'Name': name,
                'Address': address,
                'Port': port,
                'Tags': tags,
                'Meta': meta,
                'Check': check
            }
            response = requests.put(
                f'{self.base_url}/v1/agent/service/register',
                json=payload,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f'Failed to register service: {e}')
            return False

    def deregister_service(self, name):
        try:
            response = requests.put(
                f'{self.base_url}/v1/agent/service/deregister/{name}',
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_registered_services(self):
        try:
            response = requests.get(
                f'{self.base_url}/v1/agent/services',
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception:
            return {}
