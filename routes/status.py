from flask import Blueprint, jsonify
from services import HealthCheckService, ResourceService, get_health_check_config

status_bp = Blueprint('status', __name__)

@status_bp.route('/api/status/<int:resource_id>', methods=['GET'])
def get_status(resource_id):
    resource = ResourceService.get_by_id(resource_id)
    if not resource:
        return jsonify({'success': False, 'error': 'Resource not found'}), 404
    status = HealthCheckService.get_latest_status(resource_id)
    history = HealthCheckService.get_status_history(resource_id, limit=5)
    return jsonify({'success': True, 'data': {'resource': resource.to_dict(), 'latest': status, 'history': history}})

@status_bp.route('/api/check/<int:resource_id>', methods=['POST'])
def check_resource(resource_id):
    resource = ResourceService.get_by_id(resource_id)
    if not resource:
        return jsonify({'success': False, 'error': 'Resource not found'}), 404
    config = get_health_check_config()
    timeout = config.get('timeout', 5)
    result = HealthCheckService.check_and_save(resource_id, resource.url, timeout)
    return jsonify({'success': True, 'data': result})

@status_bp.route('/api/stats', methods=['GET'])
def get_stats():
    stats = HealthCheckService.get_stats()
    return jsonify({'success': True, 'data': stats})
