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
                groups_id TEXT DEFAULT NULL,
                ip TEXT,
                port1_user TEXT,
                port2_user TEXT
            )
        """)
        print("Таблица 'components' успешно создана.")
        cursor.execute("""
               CREATE TABLE IF NOT EXISTS vlan_config (
                   vlan INTEGER,
                   switchport TEXT,
                   groups_id TEXT DEFAULT NULL,
                   audience INTEGER DEFAULT NULL,
                   connection TEXT
               )
           """)
        print("Таблица 'vlan_config' успешно создана.")

        # 2. Заполнение таблицы данными
        data = [
            (1, 'Switch', 344, 'Huawei', 'Free', 'f1/0/6', 'f1/0/8', None, "10.40.83.2:2039", 'f0/5', 'f0/7'),
            (2, 'Switch', 344, 'Huawei', 'Free', 'f1/0/5', 'f1/0/7', None, "10.40.83.2:2040", 'f0/1', 'f0/3'),
            (3, 'Switch', 344, 'Cisco', 'Free', 'f1/0/1', 'f1/0/3', '1', "10.40.83.2:2036", 'f0/1', 'f0/3'),
            (4, 'Switch', 344, 'Cisco', 'Free', 'f1/0/2', 'f1/0/4', '2', "10.40.83.2:2034", 'f0/2', 'f0/4'),
            (5, 'Router', 344, 'Cisco', 'Free', 'f1/0/9', 'f1/0/11', None, "10.40.83.2:2041", 'f0/0', 'f0/1'),
            (6, 'Switch', 224, 'Cisco', 'Free', 'f0/1', 'f0/3', None, "10.40.68.3:2016", 'f0/1', 'f0/3'),
            (7, 'Switch', 224, 'Cisco', 'Free', 'f0/5', 'f0/7', None, "10.40.68.3:2018", 'f0/1', 'f0/3'),
            (8, 'Switch', 411, 'Cisco', 'Free', 'f0/1', 'f0/3', None, "10.40.131.224:2067", 'f0/1', 'f0/3'),
            (9, 'Router', 411, 'Cisco', 'Free', 'f0/5', 'f0/7', None, "10.40.131.224:2068", 'f0/0', 'f0/1'),
            (10, 'PC', 123, None, 'Free', 123, None, None, "pnet3.at.urfu.ru:30083", None, None),
            (11, 'PC', 125, None, 'Free', 125, None, None, "pnet3.at.urfu.ru:30084", None, None),
            (12, 'PC', 225, None, 'Free', 225, None, None, "pnet3.at.urfu.ru:30086", None, None),
            (13, 'PC', 223, None, 'Free', 223, None, None, "pnet3.at.urfu.ru:30093", None, None),

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
