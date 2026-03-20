from flask import Flask
import os
import threading
from models import init_db
from routes import resources_bp, consul_bp, status_bp
from services import get_app_config, get_health_check_config, ResourceService, HealthCheckService

def create_app():
    app = Flask(__name__)
    app.config['JSON_SORT_KEYS'] = False
    app.register_blueprint(resources_bp)
    app.register_blueprint(consul_bp)
    app.register_blueprint(status_bp)
    return app

def health_check_worker():
    from services import is_consul_enabled
    config = get_health_check_config()
    if not config.get('enabled', True):
        return
    interval = config.get('interval', 60)
    timeout = config.get('timeout', 5)
    while True:
        try:
            resources = ResourceService.get_all(enabled_only=True)
            for resource in resources:
                HealthCheckService.check_and_save(resource.id, resource.url, timeout)
        except Exception:
            pass
        threading.Event().wait(interval)

app = create_app()

@app.route('/')
def index():
    from flask import render_template
    return render_template('index.html')

@app.route('/add')
def add_page():
    from flask import render_template
    return render_template('add.html')

@app.route('/edit/<int:resource_id>')
def edit_page(resource_id):
    from flask import render_template
    return render_template('edit.html', resource_id=resource_id)

@app.errorhandler(404)
def not_found(e):
    from flask import jsonify
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    from flask import jsonify
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    init_db()
    config = get_health_check_config()
    if config.get('enabled', True):
        checker_thread = threading.Thread(target=health_check_worker, daemon=True)
        checker_thread.start()
    app_config = get_app_config()
    app.run(
        host=app_config.get('host', '0.0.0.0'),
        port=app_config.get('port', 5000),
        debug=app_config.get('debug', False)
    )
