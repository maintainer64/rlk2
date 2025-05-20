from typing import List, Dict, Tuple, Union

def prepare_telnet_links(devices: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Преобразует список устройств в словарь telnet-ссылок.
    Пример:
        devices = [
            {'name': 'R1', 'ip': '192.168.1.1'},
            {'name': 'SW1', 'ip': '192.168.1.2'}
        ]
        prepare_telnet_links(devices)
        # Возвращает: {'R1': 'telnet://192.168.1.1', 'SW1': 'telnet://192.168.1.2'}
    """
    telnet_links = {}

    for device in devices:
        try:
            name = device['name']
            ip = device['ip']

            # Убедимся, что IP не пустой и не None
            if not ip:
                continue

            # Добавляем схему telnet:// если её нет
            telnet_url = ip if ip.startswith('telnet://') else f'telnet://{ip}'
            telnet_links[name] = telnet_url

        except KeyError as e:
            print(f"Пропущено устройство: отсутствует ключ {e}")
            continue

    return telnet_links


def prepare_interface_mapping(raw_connections: List[Dict]) -> List[Dict[str, str]]:
    """
    Преобразует список соединений в формат interface_mapping с учетом PC(vlan) интерфейсов.
    Возвращает:
        Список словарей в формате [{"устройство1": "интерфейс1", "устройство2": "интерфейс2"}, ...]
        где для PC устройств интерфейс всегда 'en0'
    """
    interface_mapping = []

    for conn in raw_connections:
        try:
            # Инициализация переменных
            connection = {}

            # Обработка source
            if '(vlan)' in conn['source']:
                # Для PC устройств используем интерфейс 'en0'
                src_device = conn['name in source']
                src_interface = 'en0'
                connection[src_device] = src_interface
            else:
                # Для коммутаторов используем реальный интерфейс
                src_device = conn['name in source']
                src_interface = conn['source']
                connection[src_device] = src_interface

            # Обработка target
            if '(vlan)' in conn['target']:
                # Для PC устройств используем интерфейс 'en0'
                dst_device = conn['name in target']
                dst_interface = 'en0'
                connection[dst_device] = dst_interface
            else:
                # Для коммутаторов используем реальный интерфейс
                dst_device = conn['name in target']
                dst_interface = conn['target']
                connection[dst_device] = dst_interface

            interface_mapping.append(connection)

        except KeyError as e:
            print(f"Пропущено соединение: отсутствует ключ {e}")
            continue

    return interface_mapping