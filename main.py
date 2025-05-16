import os
import re
import sqlite3
import subprocess

import pandas as pd
import yaml
from flask import Flask, jsonify, request, render_template
from typing import List, Dict, Optional, Tuple, Union
import matplotlib.colors as mcolors

db_filename = 'test.db'

app = Flask(__name__)
global group_id

def run_ansible_playbook(
        playbook_path: str,
        inventory_path: str = "",
        verbose: bool = False
) -> Dict[str, Union[bool, str]]:
    """
    Выполняет Ansible playbook на КК
    :param playbook_path: Путь к файлу playbook.yml
    :param inventory_path: Путь к inventory-файлу (опционально)
    :param verbose: Вывод подробной информации
    :return: Словарь с результатами выполнения
    """

    # Проверка существования playbook
    if not os.path.exists(playbook_path):
        return {
            "success": False,
            "error": f"Playbook file not found: {playbook_path}"
        }

    # Формирование базовой команды
    command = ["ansible-playbook", playbook_path]

    # Добавление inventory файла
    if inventory_path:
        if not os.path.exists(inventory_path):
            return {
                "success": False,
                "error": f"Inventory file not found: {inventory_path}"
            }
        command.extend(["-i", inventory_path])

    # Добавление verbose режима
    if verbose:
        command.append("-vvvv")

    try:
        # Выполнение команды
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )

        return {
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }

    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "error": "Playbook execution failed",
            "stdout": e.stdout,
            "stderr": e.stderr,
            "return_code": e.returncode
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }
def lab_1(vendor = "Any"):

    devices = [
        {
            "name": "PC1",
            "device_type": "PC",
            "hosts": "-"
        },
        {
            "name": "PC2",
            "device_type": "PC",
            "hosts": "-"

        },
        {
            "name": "Switch1",
            "device_type": "Switch",
        },
        {
            "name": "Switch2",
            "device_type": "Switch",
        }
    ]

    # Топология ЛР 2
    topology = [
        {"source": "PC1(vlan)", "target": "Switch1(port1)"},
        {"source": "Switch1(port2)", "target": "Switch2(port1)"},
        {"source": "Switch2(port2)", "target": "PC2(vlan)"}
    ]
    vendor_index = 0
    for dev in devices:
        if dev["device_type"] != "PC":
            if isinstance(vendor, str):
                dev["vendor"] = vendor
            elif vendor_index < len(vendor):
                dev["vendor"] = vendor[vendor_index]
            else:
                dev["vendor"] = "Any"
            vendor_index += 1
        else:
            continue
    print(devices)
    planner(devices, topology)

def lab_2(vendor = "Any"):

    devices = [
        {
            "name": "PC1",
            "device_type": "PC",
            "hosts": "-"
        },
        {
            "name": "PC2",
            "device_type": "PC",
            "hosts": "-"

        },
        {
            "name": "Router1",
            "device_type": "Router",
        },
        {
            "name": "Router2",
            "device_type": "Router",
        }
    ]

    # Топология ЛР 2
    topology = [
        {"source": "PC1(vlan)", "target": "Router1(port1)"},
        {"source": "Router1(port2)", "target": "Router2(port1)"},
        {"source": "Router2(port2)", "target": "PC2(vlan)"}
    ]
    vendor_index = 0
    for dev in devices:
        if dev["device_type"] != "PC":
            if isinstance(vendor, str):
                dev["vendor"] = vendor
            elif vendor_index < len(vendor):
                dev["vendor"] = vendor[vendor_index]
            else:
                dev["vendor"] = "Any"
            vendor_index += 1
        else:
            continue
    print(devices)
    planner(devices, topology)

def update_topology(devices,topology) -> bool:
    vlans = free_vm(len(topology))
    for top in topology:
        for device in devices:
            if device['name'] in top["source"]:
                if device["device_type"] == 'PC':
                    top["vlan"] = device["port1"]
                if "(port2)" in top["source"]:
                    top["source"] = device["port2"]
                elif "(port1)" in top["source"]:
                    top["source"] = device["port1"]
                top["host in source"] = device["hosts"]
            if device['name'] in top["target"]:
                if device["device_type"] == 'PC':
                    top["vlan"] = device["port1"]
                if "(port2)" in top["target"]:
                    top["target"] = device["port2"]
                elif "(port1)" in top["target"]:
                    top["target"] = device["port1"]
                top["host in target"] = device["hosts"]
        if 'vlan' not in top:
            top["vlan"] = vlans.pop()[0]



def planner(devices,topology):
    group_id = update_bd(devices)
    if group_id == False:
        return False
    update_topology(devices,topology)
    if group_id != False:
        create_playbook(topology, group_id)
        run_playbook()
def update_bd(devices) -> int:
    try:
        with sqlite3.connect(db_filename) as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION;")
            group_id = max_groups_id() + 1
            for device in devices:
                # Проверка доступности
                if device["device_type"] != 'PC':
                    if device["vendor"] != "Any":
                        available_devices = cursor.execute(
                            """SELECT COUNT(*), component_id, location,port1,port2 FROM components
                            WHERE component_type=? AND model=? AND status=?
                            ORDER BY RANDOM() 
                            LIMIT 1
                            """, (device["device_type"], device["vendor"], "Free")).fetchone()
                        device["hosts"] = (available_devices[2])
                        device["port1"] = (available_devices[3])
                        device["port2"] = (available_devices[4])
                    else:
                        available_devices = cursor.execute(
                            """SELECT COUNT(*), component_id, location,port1,port2 FROM components
                            WHERE component_type=? AND status=?
                            ORDER BY RANDOM() 
                            LIMIT 1
                            """, (device["device_type"], "Free")).fetchone()
                        device["hosts"] = (available_devices[2])
                        device["port1"] = (available_devices[3])
                        device["port2"] = (available_devices[4])
                else:
                    available_devices = cursor.execute(
                        """SELECT COUNT(*), component_id, location, port1 FROM components
                        WHERE component_type=? AND status=?
                        ORDER BY RANDOM() 
                        LIMIT 1
                        """, (device["device_type"], "Free")).fetchone()
                    device["hosts"] = "no host"
                    device["port1"] = available_devices[3]
                if available_devices[0]:
                    # Если устройство доступно, обновляем статус
                    cursor.execute(
                       """UPDATE components
                           SET status=?, groups_id = ?
                           WHERE component_id=?
                        """, ('Active', group_id, available_devices[1]))

                else:
                    print("Оборудование отсутствует!")
                    conn.rollback()
                    return False
            conn.commit()
        return group_id
    except Exception as e:
        print(f"Ошибка: {e}")

def run_playbook():
# Запуск playbook с inventory и переменными
    result = run_ansible_playbook(
        playbook_path="vlan_playbook.yaml",
        inventory_path="inventory.ini",
        verbose=True
    )
    if result["success"]:
        print("Playbook выполнен успешно!")
        print(result["stdout"])
    else:
        print("Ошибка выполнения playbook:")
        print(result.get("error", ""))
        print(result["stderr"])

def free_vm(count) -> List[Tuple[int]]:
    """Возвращает указанное количество свободных VLAN."""
    used_vlans = get_used_vlans()
    available_vlans = []

    # Ищем свободные VLAN в диапазоне 10-1000 с шагом 10
    for vlan in range(10, 1001, 10):
        if vlan not in used_vlans:
            available_vlans.append((vlan,))
            if len(available_vlans) == count:
                break

    return available_vlans if len(available_vlans) >= count else []

def get_used_vlans() -> List[int]:
    """Возвращает список занятых VLAN из базы данных."""
    try:
        with sqlite3.connect('test.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT vlan FROM vlan_config WHERE groups_id != 0")
            return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Ошибка при получении занятых VLAN: {e}")
        return []
def get_group_name(auditorium):
    """
    Определяет группу Ansible на основе audience_id.
     """
    if auditorium == 224:
        return "KK-224"
    elif auditorium == 344:
        return "KK-344"
    else:
        return "group_unknown"

def create_playbook(topology, group_id, output_file="vlan_playbook.yaml"):
    playbook = []
    device_group = {}
    for top in topology:
        if "PC" not in top["source"]:
            auditorium = get_group_name(top["host in source"])
            if auditorium not in device_group:
                device_group[auditorium] = {'hosts': auditorium, 'gather_facts': 'no', 'tasks': []}
            add_vlan_task(device_group, auditorium, top["source"], top["vlan"])
            add_vlan(top["vlan"], top["source"], group_id, auditorium)
        if "PC" not in top["target"]:
            auditorium = get_group_name(top["host in target"])
            if auditorium not in device_group:
                device_group[auditorium] = {'hosts': auditorium, 'gather_facts': 'no', 'tasks': []}
            add_vlan_task(device_group, auditorium, top["target"], top["vlan"])
            add_vlan(top["vlan"], top["target"], group_id, auditorium)
    print(device_group)
    # Преобразуем словарь групп в список плейбучных заданий
    playbook.extend(list(device_group.values()))

    try:
        # Конвертирование плейбука в YAML и запись в файл
        playbook_yaml = yaml.dump(playbook, indent=2, allow_unicode=True)
        with open(output_file, "w", encoding='utf-8') as f:
            f.write(playbook_yaml)
        return True
    except Exception as e:
        print(f"Ошибка при записи playbook в файл: {e}")
        return False

def add_vlan(vlan, switchport, groups_id, audience):
    try:
        with sqlite3.connect('test.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vlan_config (vlan, switchport, groups_id, audience)
                VALUES (?, ?, ?, ?)
            """, (vlan, switchport, groups_id, audience))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении VLAN: {e}")
    finally:
        if conn:
            conn.close()

def add_vlan_task(device_group, group_name, interface_name, vlan):
    task = {
        'name': f"Настройка порта {interface_name} в VLAN {vlan}",
        'ios_config': {
            'parents': f"interface {interface_name}",
            'lines': [
                "switchport mode access",
                f"switchport access vlan {vlan}",
                "no cdp enable",
            ],
        },
    }
    device_group[group_name]['tasks'].append(task)
def max_groups_id():
    try:
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        result = cursor.execute("""
            SELECT MAX(groups_id) 
            FROM components 
            WHERE groups_id IS NOT NULL
        """)
        group_id = result.fetchone()[0]
        cursor.close()
        conn.close()
        if group_id:
            return (group_id)
        else:
            return 0
    except Exception as e:
        print(f"Произошла ошибка: {e}")

def clear_vlan(groups_id, output_file="vlan_playbook.yaml"):
    try:
        with sqlite3.connect('test.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM vlan_config
                WHERE groups_id = ?
                """, (groups_id,)
            )

            available_devices = cursor.fetchall()
            cursor.execute(
                """DELETE FROM vlan_config
                   WHERE groups_id = ?     
                """, (groups_id,)
            )

            conn.commit()
            print(f"Удалено {cursor.rowcount} записей с groups_id = {groups_id}")
            playbook = []
            device_group = {}
            for device in available_devices:
                print(device)
                auditorium = device[3]
                if auditorium not in device_group:
                    device_group[auditorium] = {'hosts': auditorium, 'gather_facts': 'no', 'tasks': []}
                del_vlan_task(device_group, auditorium, device[1], device[0])
            playbook.extend(list(device_group.values()))
            try:
                playbook_yaml = yaml.dump(playbook, indent=2, allow_unicode=True)
                with open(output_file, "w", encoding='utf-8') as f:
                    f.write(playbook_yaml)
                return True
            except Exception as e:
                print(f"Ошибка при записи playbook в файл: {e}")
                return False
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении VLAN: {e}")
    finally:
        if conn:
            conn.close()

def del_vlan_task(device_group, group_name, interface_name, vlan):
    task = {
        'name': f"Настройка порта {interface_name} в VLAN {vlan}",
        'ios_config': {
            'parents': f"interface {interface_name}",
            'lines': [
                "no switchport mode access",
                f"no switchport access vlan {vlan}",
                "cdp enable",
            ],
        },
    }
    device_group[group_name]['tasks'].append(task)


def clear_bd(groups_id, db_filename = 'test.db'):  # Добавим db_filename как параметр
    conn = None  # Инициализируем conn вне try
    try:
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        query = "UPDATE components SET status = 'Free' WHERE status = 'Active' AND `groups_id` = ?"
        cursor.execute(query, (groups_id,))
        conn.commit()
        print(f"Обновлено {cursor.rowcount} записей в components.")
        try:
            clear_vlan(groups_id)
        except Exception as e:
            print(f"Ошибка при вызове clear_vlan: {e}")
            # Решите, нужно ли продолжать или прервать выполнение

    except sqlite3.Error as e:
        print(f"Произошла ошибка при работе с базой данных: {e}")
    finally:
        if conn:
            conn.close()


@app.route('/')
def generate_table():
    conn = None
    try:
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        audiences = [224, 344, 411]  # Аудитории для отображения

        table_data = {}
        for aud in audiences:
            cursor.execute(
                "SELECT component_type, model, status, groups_id FROM components WHERE location = ?", (aud,)
            )
            devices = cursor.fetchall()

            for i, device in enumerate(devices):
                component_type, model, status, group_id = device
                device_name = f"{component_type[0]}{i + 1}-{model}"
                if status == 'Active' and group_id is not None:
                    device_name += f" (G{group_id})"
                table_data.setdefault(aud, []).append((device_name, status))

        max_rows = max(len(table_data.get(aud, [])) for aud in audiences)

        cell_text = []
        colors = []

        for i in range(max_rows):
            row_text = []
            row_colors = []
            for aud in audiences:
                if i < len(table_data.get(aud, [])):
                    device_name, status = table_data[aud][i]
                    row_text.append(device_name)
                    if status == 'Active':
                        row_colors.append(mcolors.to_hex('yellow'))
                    elif status == 'Free':
                        row_colors.append(mcolors.to_hex('lightgreen'))
                    else:
                        row_colors.append(mcolors.to_hex('lightcoral'))
                else:
                    row_text.append('')
                    row_colors.append('white')
            cell_text.append(row_text)
            colors.append(row_colors)

        col_labels = [f"P{aud}" for aud in audiences]

        return render_template('table.html', col_labels=col_labels, cell_text=cell_text, colors=colors)

    finally:
        if conn:
            conn.close()


@app.route('/api/clear_db', methods=['POST'])
def api_clear_db():
    """API endpoint to clear the database for a specific group"""
    try:
        data = request.get_json()
        group_id = data.get('group_id')

        if not group_id:
            return jsonify({
                'status': 'error',
                'message': 'group_id is required'
            }), 400

        clear_bd(group_id)
        return jsonify({
            'status': 'success',
            'message': f'Database cleared for group {group_id}'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/run_lab', methods=['POST'])
def api_run_lab():
    """API endpoint to run a specific lab work"""
    try:
        data = request.get_json()
        lab_number = data.get('lab_number')
        vendor = data.get('vendor')

        if not lab_number:
            return jsonify({
                'status': 'error',
                'message': 'lab_number is required'
            }), 400

        if lab_number == 1:
            lab_1(vendor) if vendor else lab_1()
            return jsonify({
                'status': 'success',
                'message': 'Lab 1 executed successfully'
            })
        # Add more labs here as needed
        else:
            return jsonify({
                'status': 'error',
                'message': f'Lab {lab_number} not implemented'
            }), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)






#curl -X POST -H "Content-Type: application/json" -d '{"lab_number":1, "vendor":"Cisco"}' http://localhost:5000/api/run_lab

#curl -X POST -H "Content-Type: application/json" -d '{"group_id":1}' http://localhost:5000/api/clear_db

#curl http://localhost:5000/api/generate_table
#curl -X POST http://10.40.225.6:5001/api/run_lab -H "Content-Type: application/json" -d "{""lab_number"": 1}"
#curl -X POST http://10.40.225.6:5005/api/clear_db -H "Content-Type: application/json" -d "{""group_id"": 1}"





