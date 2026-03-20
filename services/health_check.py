import requests
import time
from models import get_db_context
from datetime import datetime

class HealthCheckService:

    @staticmethod
    def check_resource(url, timeout=5):
        start_time = time.time()
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            response_time = (time.time() - start_time) * 1000
            is_online = response.status_code < 500
            return {
                'status': 'online' if is_online else 'offline',
                'response_time': round(response_time, 2),
                'status_code': response.status_code
            }
        except requests.exceptions.Timeout:
            return {'status': 'offline', 'response_time': timeout * 1000, 'status_code': 0, 'error': 'timeout'}
        except requests.exceptions.ConnectionError:
            return {'status': 'offline', 'response_time': 0, 'status_code': 0, 'error': 'connection_error'}
        except Exception as e:
            return {'status': 'offline', 'response_time': 0, 'status_code': 0, 'error': str(e)}

    @staticmethod
    def check_and_save(resource_id, url, timeout=5):
        result = HealthCheckService.check_resource(url, timeout)
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO resource_status (resource_id, status, response_time, checked_at)
                VALUES (?, ?, ?, ?)
            ''', (resource_id, result['status'], result['response_time'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        return result

    @staticmethod
    def get_latest_status(resource_id):
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT status, response_time, checked_at
                FROM resource_status
                WHERE resource_id = ?
                ORDER BY checked_at DESC
                LIMIT 1
            ''', (resource_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'status': row['status'],
                    'response_time': row['response_time'],
                    'checked_at': row['checked_at']
                }
            return None

    @staticmethod
    def get_status_history(resource_id, limit=10):
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT status, response_time, checked_at
                FROM resource_status
                WHERE resource_id = ?
                ORDER BY checked_at DESC
                LIMIT ?
            ''', (resource_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_stats():
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as total FROM resources WHERE is_enabled = 1')
            total = cursor.fetchone()['total']

            cursor.execute('''
                SELECT COUNT(DISTINCT rs.resource_id) as online
                FROM resource_status rs
                INNER JOIN resources r ON r.id = rs.resource_id
                WHERE r.is_enabled = 1 
                AND rs.status = 'online'
                AND rs.checked_at = (
                    SELECT MAX(checked_at) FROM resource_status WHERE resource_id = rs.resource_id
                )
            ''')
            online = cursor.fetchone()['online']

            cursor.execute('''
                SELECT AVG(response_time) as avg_time FROM resource_status
                WHERE status = 'online' AND checked_at > datetime('now', '-1 hour')
            ''')
            avg_row = cursor.fetchone()
            avg_response_time = avg_row['avg_time'] if avg_row['avg_time'] else 0

            return {
                'total': total,
                'online': online,
                'offline': total - online,
                'avg_response_time': round(avg_response_time, 2) if avg_response_time else 0
            }
