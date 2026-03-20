import sqlite3
from datetime import datetime
from contextlib import contextmanager
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'data', 'zhub.db')

class Resource:
    def __init__(self, row):
        if row:
            self.id = row['id']
            self.name = row['name']
            self.url = row['url']
            self.category = row['category']
            self.group_name = row['group_name']
            self.tags = row['tags']
            self.description = row['description']
            self.is_enabled = bool(row['is_enabled'])
            self.consul_enabled = bool(row['consul_enabled'])
            try:
                self.consul_check_type = row['consul_check_type']
            except (KeyError, IndexError):
                self.consul_check_type = 'http'
            try:
                self.consul_check_interval = row['consul_check_interval']
            except (KeyError, IndexError):
                self.consul_check_interval = '30s'
            try:
                self.consul_tags = row['consul_tags']
            except (KeyError, IndexError):
                self.consul_tags = ''
            self.created_at = row['created_at']
            self.updated_at = row['updated_at']
        else:
            self.id = None

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'category': self.category,
            'group_name': self.group_name,
            'tags': self.tags,
            'description': self.description,
            'is_enabled': self.is_enabled,
            'consul_enabled': self.consul_enabled,
            'consul_check_type': self.consul_check_type,
            'consul_check_interval': self.consul_check_interval,
            'consul_tags': self.consul_tags,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def __bool__(self):
        return self.id is not None

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db_context():
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                url VARCHAR(500) NOT NULL,
                category VARCHAR(50) NOT NULL DEFAULT 'other',
                group_name VARCHAR(100) DEFAULT '',
                tags VARCHAR(200) DEFAULT '',
                description TEXT DEFAULT '',
                is_enabled INTEGER DEFAULT 1,
                consul_enabled INTEGER DEFAULT 0,
                consul_check_type VARCHAR(20) DEFAULT 'http',
                consul_check_interval VARCHAR(20) DEFAULT '30s',
                consul_tags VARCHAR(200) DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resource_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER NOT NULL,
                status VARCHAR(20) NOT NULL,
                response_time FLOAT DEFAULT 0,
                checked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_resource_category ON resources(category)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status_resource ON resource_status(resource_id)
        ''')
