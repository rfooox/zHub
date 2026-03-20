from flask import Blueprint, request, jsonify
from services import ConsulService, ResourceService, is_consul_enabled, get_consul_config

consul_bp = Blueprint('consul', __name__)

@consul_bp.route('/api/consul/status', methods=['GET'])
def consul_status():
    if not is_consul_enabled():
        return jsonify({'success': True, 'data': {'enabled': False}})
    consul = ConsulService()
    available = consul.is_available()
    registered = {}
    if available:
        registered = consul.get_registered_services()
    return jsonify({
        'success': True,
        'data': {
            'enabled': True,
            'available': available,
            'host': consul.host,
            'port': consul.port,
            'registered_count': len(registered)
        }
    })

@consul_bp.route('/api/consul/services', methods=['GET'])
def get_consul_services():
    if not is_consul_enabled():
        return jsonify({'success': False, 'error': 'Consul is not enabled'}), 400
    consul = ConsulService()
    services = consul.get_services()
    return jsonify({'success': True, 'data': services})

@consul_bp.route('/api/consul/service/<service_name>', methods=['GET'])
def get_consul_service(service_name):
    if not is_consul_enabled():
        return jsonify({'success': False, 'error': 'Consul is not enabled'}), 400
    consul = ConsulService()
    health_info = consul.get_service_health(service_name)
    return jsonify({'success': True, 'data': health_info})

@consul_bp.route('/api/consul/sync-to-consul', methods=['POST'])
def sync_to_consul():
    if not is_consul_enabled():
        return jsonify({'success': False, 'error': 'Consul is not enabled'}), 400
    data = request.get_json() or {}
    resource_ids = data.get('resource_ids', [])
    consul = ConsulService()
    if not consul.is_available():
        return jsonify({'success': False, 'error': 'Cannot connect to Consul'}), 400
    config = get_consul_config()
    sync_config = config.get('sync', {})
    default_ttl = sync_config.get('default_ttl', '30s')
    default_tags = sync_config.get('tags', [])
    if resource_ids:
        resources = [ResourceService.get_by_id(rid) for rid in resource_ids]
        resources = [r for r in resources if r]
    else:
        resources = ResourceService.get_all(enabled_only=True)
    synced = 0
    failed = []
    for resource in resources:
        if not resource.consul_enabled:
            continue
        tags = default_tags[:]
        if resource.consul_tags:
            tags.extend([t.strip() for t in resource.consul_tags.split(',') if t.strip()])
        if resource.tags:
            tags.extend([t.strip() for t in resource.tags.split(',') if t.strip()])
        if resource.category:
            tags.append(resource.category)
        meta = {'zhub_id': str(resource.id), 'category': resource.category, 'group': resource.group_name or ''}
        check_type = getattr(resource, 'consul_check_type', 'http') or 'http'
        check_interval = getattr(resource, 'consul_check_interval', '30s') or '30s'
        success = consul.register_service(
            name=resource.name, url=resource.url, tags=tags, meta=meta,
            check_type=check_type, interval=check_interval
        )
        if success:
            ResourceService.update(resource.id, consul_enabled=True)
            synced += 1
        else:
            failed.append(resource.name)
    return jsonify({'success': True, 'data': {'synced': synced, 'failed': failed}})

@consul_bp.route('/api/consul/sync-from-consul', methods=['POST'])
def sync_from_consul():
    if not is_consul_enabled():
        return jsonify({'success': False, 'error': 'Consul is not enabled'}), 400
    consul = ConsulService()
    if not consul.is_available():
        return jsonify({'success': False, 'error': 'Cannot connect to Consul'}), 400
    services = consul.get_services()
    synced_count = 0
    for service_name, tags in services.items():
        health_info = consul.get_service_health(service_name)
        for instance in health_info:
            url = f"http://{instance['address']}:{instance['port']}"
            existing = ResourceService.get_all(search=service_name, enabled_only=False)
            if not any(r.name == service_name for r in existing):
                ResourceService.create(
                    name=service_name, url=url, category='consul',
                    group_name=instance.get('node', 'unknown'),
                    tags=','.join(tags) if tags else 'consul',
                    description=f"Consul service: {service_name}", is_enabled=True
                )
                synced_count += 1
    return jsonify({'success': True, 'data': {'synced': synced_count}})

@consul_bp.route('/api/consul/deregister/<service_name>', methods=['POST'])
def deregister_service(service_name):
    if not is_consul_enabled():
        return jsonify({'success': False, 'error': 'Consul is not enabled'}), 400
    consul = ConsulService()
    success = consul.deregister_service(service_name)
    if success:
        resources = ResourceService.get_all(search=service_name, enabled_only=False)
        for r in resources:
            if r.consul_enabled:
                ResourceService.update(r.id, consul_enabled=False)
    return jsonify({'success': success})
