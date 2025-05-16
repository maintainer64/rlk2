import sqlite3
import os

def create_and_populate_database(db_filename="test.db"):
    conn = None  # Инициализация conn вне блока try
    try:
        # Удаляем базу данных, если она существует (чтобы гарантировать создание с новой схемой)
        if os.path.exists(db_filename):
            os.remove(db_filename)
            print(f"Удалена существующая база данных '{db_filename}'.")

        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()

        # 1. Создание таблицы components (если она еще не существует)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS components (
                component_id INTEGER PRIMARY KEY,
                component_type TEXT,
                location INTEGER,
                model TEXT,
                status TEXT,
                port1 TEXT,
                port2 TEXT,
                groups_id INTEGER DEFAULT NULL
            )
        """)
        print("Таблица 'components' успешно создана.")
        cursor.execute("""
               CREATE TABLE IF NOT EXISTS vlan_config (
                   vlan INTEGER,
                   switchport TEXT,
                   groups_id INTEGER DEFAULT NULL,
                   audience INTEGER DEFAULT NULL
               )
           """)
        print("Таблица 'vlan_config' успешно создана.")

        # 2. Заполнение таблицы данными
        data = [
            (1, 'Switch', 344, 'Huawei', 'Free', 'Fa1/0/36', 'Fa1/0/37', None),
            (2, 'Switch', 224, 'Cisco', 'Free', 'Fa0/20', 'Fa0/21', None),
            (3, 'PC', 71, None, 'Free', 71, None, None),
            (4, 'PC', 72, None, 'Free', 72, None, None),

        ]

        cursor.executemany("""
            INSERT INTO components (component_id, component_type, location, model, status, port1, port2, groups_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?) 
        """, data)
        print("Данные успешно вставлены в таблицу 'components'.")

        # 4. Сохранение изменений и закрытие соединения
        conn.commit()
        print(f"База данных '{db_filename}' успешно создана и заполнена.")

    except sqlite3.Error as e:
        print(f"Ошибка при работе с базой данных: {e}")

    finally:
        if conn:
            conn.close()

# Пример использования:
if __name__ == "__main__":
    create_and_populate_database()