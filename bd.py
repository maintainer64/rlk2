import os
import sqlite3

from unl_store import unl_table_create


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
                groups_id INTEGER DEFAULT NULL,
                ip TEXT
            )
        """)
        print("Таблица 'components' успешно создана.")
        cursor.execute("""
               CREATE TABLE IF NOT EXISTS vlan_config (
                   vlan INTEGER,
                   switchport TEXT,
                   groups_id INTEGER DEFAULT NULL,
                   audience INTEGER DEFAULT NULL,
                   connection TEXT                   
               )
           """)
        print("Таблица 'vlan_config' успешно создана.")

        # 2. Заполнение таблицы данными
        data = [
            (1, 'Switch', 344, 'Cisco', 'Free', 'Fa1/0/36', 'Fa1/0/37', None, "10.20.121.21"),
            (4, 'Switch', 224, 'Cisco', 'Free', 'Fa0/20', 'Fa0/21', None, "10.20.121.21"),
            (5, 'Router', 344, 'Cisco', 'Free', 'Fa1/0/32', 'Fa1/0/33', None, "10.20.121.21"),
            (6, 'Router', 224, 'Cisco', 'Free', 'Fa0/11', 'Fa0/12', None, "10.20.121.21"),

            (7, 'PC', 71, None, 'Free', 71, None, None, "10.20.121.21"),
            (8, 'PC', 72, None, 'Free', 72, None, None, "10.20.121.21"),

        ]

        cursor.executemany("""
            INSERT INTO components (component_id, component_type, location, model, status, port1, port2, groups_id, ip)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) 
        """, data)
        print("Данные успешно вставлены в таблицу 'components'.")

        unl_table_create(db=conn)
        print("Создание таблицы 'files'")

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
