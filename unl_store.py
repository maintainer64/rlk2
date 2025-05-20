from sqlite3 import Connection
from typing import Optional


def unl_table_create(db: Connection) -> None:
    """Создает таблицу, если она не существует"""
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            groups_id TEXT PRIMARY KEY,
            content BLOB NOT NULL
        )
    ''')
    db.commit()
    return None


def unl_file_save_or_update(db: Connection, groups_id: str, content: bytes) -> None:
    """Сохраняет или обновляет файл в базе данных"""
    cursor = db.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO files (groups_id, content)
        VALUES (?, ?)
    ''', (groups_id, content))
    db.commit()
    return None


def unl_file_delete(db: Connection, groups_id: str) -> None:
    """Удаляет файл из базы данных по group_id"""
    cursor = db.cursor()
    cursor.execute('DELETE FROM files WHERE groups_id = ?', (groups_id,))
    db.commit()
    return None


def unl_file_content_get(db: Connection, groups_id: str) -> Optional[bytes]:
    """Получает содержимое файла по group_id или возвращает None"""
    cursor = db.cursor()
    cursor.execute('SELECT content FROM files WHERE groups_id = ?', (groups_id,))
    result = cursor.fetchone()
    return result[0] if result else None
