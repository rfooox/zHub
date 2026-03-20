from datetime import datetime
from models import get_db_context, Resource

class ResourceService:

    @staticmethod
    def get_all(category=None, group=None, search=None, enabled_only=True):
        with get_db_context() as conn:
            cursor = conn.cursor()
            sql = 'SELECT * FROM resources WHERE 1=1'
            params = []
            if category:
                sql += ' AND category = ?'
                params.append(category)
            if group:
                sql += ' AND group_name = ?'
                params.append(group)
            if search:
                sql += ' AND (name LIKE ? OR url LIKE ? OR description LIKE ?)'
                pattern = f'%{search}%'
                params.extend([pattern, pattern, pattern])
            if enabled_only:
                sql += ' AND is_enabled = 1'
            sql += ' ORDER BY category, group_name, name'
            cursor.execute(sql, params)
            return [Resource(row) for row in cursor.fetchall()]

    @staticmethod
    def get_by_id(resource_id):
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM resources WHERE id = ?', (resource_id,))
            row = cursor.fetchone()
            return Resource(row) if row else None

    @staticmethod
    def create(name, url, category='other', group_name='', tags='', description='', is_enabled=True, 
               consul_enabled=False, consul_check_type='http', consul_check_interval='30s', consul_tags=''):
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO resources (name, url, category, group_name, tags, description, is_enabled, 
                                     consul_enabled, consul_check_type, consul_check_interval, consul_tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, url, category, group_name, tags, description, 
                  1 if is_enabled else 0, 1 if consul_enabled else 0,
                  consul_check_type, consul_check_interval, consul_tags))
            return cursor.lastrowid

    @staticmethod
    def update(resource_id, **kwargs):
        allowed_fields = ['name', 'url', 'category', 'group_name', 'tags', 'description', 
                         'is_enabled', 'consul_enabled', 'consul_check_type', 'consul_check_interval', 'consul_tags']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False
        if 'is_enabled' in updates:
            updates['is_enabled'] = 1 if updates['is_enabled'] else 0
        if 'consul_enabled' in updates:
            updates['consul_enabled'] = 1 if updates['consul_enabled'] else 0
        updates['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with get_db_context() as conn:
            cursor = conn.cursor()
            set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
            cursor.execute(f'UPDATE resources SET {set_clause} WHERE id = ?', list(updates.values()) + [resource_id])
            return cursor.rowcount > 0

    @staticmethod
    def delete(resource_id):
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM resources WHERE id = ?', (resource_id,))
            return cursor.rowcount > 0

    @staticmethod
    def get_categories():
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT category FROM resources WHERE category != "" ORDER BY category')
            return [row[0] for row in cursor.fetchall()]

    @staticmethod
    def get_groups():
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT group_name FROM resources WHERE group_name != "" ORDER BY group_name')
            return [row[0] for row in cursor.fetchall()]
