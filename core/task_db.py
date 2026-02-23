import sqlite3
import threading
import functools
import json
from datetime import datetime

def synchronized(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        with self.lock:
            return func(self, *args, **kwargs)
    return wrapper

class Task_Db:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Task_Db, cls).__new__(cls)
                    cls._instance.lock = threading.Lock()
                    cls._instance.init_db()
        return cls._instance

    def init_db(self):
        conn = sqlite3.connect('tasks.db', check_same_thread=False)
        c = conn.cursor()
        # status: pending, processing, completed, failed
        c.execute('''CREATE TABLE IF NOT EXISTS tasks
            (id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            status TEXT NOT NULL,
            result TEXT,
            error TEXT,
            created_at TEXT,
            updated_at TEXT
            );''')
        conn.commit()
        conn.close()

    def get_connection(self):
        return sqlite3.connect('tasks.db', check_same_thread=False)

    @synchronized
    def add_task(self, task_id, task_type):
        conn = self.get_connection()
        try:
            c = conn.cursor()
            now = datetime.now().isoformat()
            c.execute('INSERT INTO tasks (id, type, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)', 
                      (task_id, task_type, 'pending', now, now))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding task: {e}")
            return False
        finally:
            conn.close()

    @synchronized
    def update_task_status(self, task_id, status, result=None, error=None):
        conn = self.get_connection()
        try:
            c = conn.cursor()
            now = datetime.now().isoformat()
            
            update_fields = ['status = ?', 'updated_at = ?']
            params = [status, now]
            
            if result is not None:
                update_fields.append('result = ?')
                params.append(json.dumps(result) if isinstance(result, (dict, list)) else result)
            
            if error is not None:
                update_fields.append('error = ?')
                params.append(str(error))
                
            params.append(task_id)
            
            sql = f'UPDATE tasks SET {", ".join(update_fields)} WHERE id = ?'
            c.execute(sql, params)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating task: {e}")
            return False
        finally:
            conn.close()

    def get_task(self, task_id):
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            row = c.fetchone()
            if row:
                columns = [col[0] for col in c.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            print(f"Error getting task: {e}")
            return None
        finally:
            conn.close()

    def get_tasks_by_type(self, task_type, limit=10):
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute('SELECT * FROM tasks WHERE type = ? ORDER BY created_at DESC LIMIT ?', (task_type, limit))
            rows = c.fetchall()
            columns = [col[0] for col in c.description]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Error getting tasks: {e}")
            return []
        finally:
            conn.close()

    def get_recent_success_tasks(self, limit=10):
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("SELECT * FROM tasks WHERE status = 'completed' ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = c.fetchall()
            columns = [col[0] for col in c.description]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Error getting recent tasks: {e}")
            return []
        finally:
            conn.close()
