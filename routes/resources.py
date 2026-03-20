from flask import Blueprint, request, jsonify
from services import ResourceService, HealthCheckService, is_consul_enabled

resources_bp = Blueprint('resources', __name__)

@resources_bp.route('/api/resources', methods=['GET'])
def get_resources():
    category = request.args.get('category')
    group = request.args.get('group')
    search = request.args.get('search')
    resources = ResourceService.get_all(category=category, group=group, search=search)
    result = []
    for r in resources:
        res_dict = r.to_dict()
        if is_consul_enabled():
            status = HealthCheckService.get_latest_status(r.id)
            res_dict['health_status'] = status
        else:
            res_dict['health_status'] = None
        result.append(res_dict)
    return jsonify({'success': True, 'data': result})

@resources_bp.route('/api/resources/<int:resource_id>', methods=['GET'])
def get_resource(resource_id):
    resource = ResourceService.get_by_id(resource_id)
    if not resource:
        return jsonify({'success': False, 'error': 'Resource not found'}), 404
    res_dict = resource.to_dict()
    if is_consul_enabled():
        status = HealthCheckService.get_latest_status(resource_id)
        res_dict['health_status'] = status
    else:
        res_dict['health_status'] = None
    return jsonify({'success': True, 'data': res_dict})

@resources_bp.route('/api/resources', methods=['POST'])
def create_resource():
    data = request.get_json()
    if not data.get('name') or not data.get('url'):
        return jsonify({'success': False, 'error': 'Name and URL are required'}), 400
    resource_id = ResourceService.create(
        name=data['name'],
        url=data['url'],
        category=data.get('category', 'other'),
        group_name=data.get('group_name', ''),
        tags=data.get('tags', ''),
        description=data.get('description', ''),
        is_enabled=data.get('is_enabled', True)
    )
    return jsonify({'success': True, 'data': {'id': resource_id}}), 201

@resources_bp.route('/api/resources/<int:resource_id>', methods=['PUT'])
def update_resource(resource_id):
    data = request.get_json()
    resource = ResourceService.get_by_id(resource_id)
    if not resource:
        return jsonify({'success': False, 'error': 'Resource not found'}), 404
    ResourceService.update(resource_id, **data)
    return jsonify({'success': True})

@resources_bp.route('/api/resources/<int:resource_id>', methods=['DELETE'])
def delete_resource(resource_id):
    if not ResourceService.get_by_id(resource_id):
        return jsonify({'success': False, 'error': 'Resource not found'}), 404
    ResourceService.delete(resource_id)
    return jsonify({'success': True})

@resources_bp.route('/api/categories', methods=['GET'])
def get_categories():
    categories = ResourceService.get_categories()
    return jsonify({'success': True, 'data': categories})

@resources_bp.route('/api/groups', methods=['GET'])
def get_groups():
    groups = ResourceService.get_groups()
    return jsonify({'success': True, 'data': groups})
