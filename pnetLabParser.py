import base64
import hashlib
import re
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from bs4 import BeautifulSoup


@dataclass
class TemplateParams:
    template_path: Path
    lab_name: str
    telnet_links: Dict[str, str]
    interface_mapping: List[Dict[str, str]]
    debug: bool = False


def debug_log(message: str, params: TemplateParams) -> None:
    """Вывод отладочных сообщений только в режиме debug"""
    if params.debug:
        print(f"[DEBUG] {message}")


def create_iframe_workbooks(iframe_url) -> str:
    if not iframe_url:
        return ""
    inject_html = f"""
    <style>
        .wb-body .ck-content.box_padding{{
        height: 100%;
        padding: 0;
        overflow: hidden;
        }}
    </style>
    <iframe src="{iframe_url}" positionable="true" style="
        position: relative;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: none;
        margin: 0;
        padding: 0;
        overflow: hidden;
        z-index: 9999;
      " frameborder="0" allowfullscreen></iframe>
    """
    return base64.b64encode(inject_html.encode("utf-8")).decode("utf-8")


def create_lab_xml(lab_name: str, physical_topology_base64: str, workbook_base64: str) -> bytes:
    """Создание UNL-файла с топологией"""
    guid = str(uuid.uuid4())
    lab = ET.Element("lab", {
        "name": lab_name,
        "id": guid,
        "version": "1",
        "scripttimeout": "300",
        "password": hashlib.md5(guid.encode()).hexdigest(),
        "author": "1",
        "countdown": "60",
        "darkmode": "",
        "mode3d": "",
        "nogrid": "",
        "joinable": "2",
        "joinable_emails": "admin",
        "openable": "2",
        "openable_emails": "admin",
        "editable": "2",
        "editable_emails": "admin",
        "multi_config_active": ""
    })

    ET.SubElement(lab, "topology")
    objects = ET.SubElement(lab, "objects")
    textobjects = ET.SubElement(objects, "textobjects")
    textobject = ET.SubElement(textobjects, "textobject", {
        "id": "physical-topology",
        "name": "physical",
        "type": "text"
    })
    data = ET.SubElement(textobject, "data")
    data.text = physical_topology_base64
    workbooks = ET.SubElement(lab, "workbooks")
    if workbook_base64:
        textobject = ET.SubElement(workbooks, "workbook", {
            "id": "Manual",
            "weight": "0",
            "type": "html"
        })
        content = ET.SubElement(textobject, "content")
        page = ET.SubElement(content, "page")
        page.text = workbook_base64
    return ET.tostring(lab, xml_declaration=True, encoding='utf-8')


def clean_html_content(content: str) -> str:
    """Очистка HTML контента"""
    content = re.sub(r'[\r\n\t]+', ' ', content)
    content = re.sub(r'[ ]{2,}', ' ', content)
    return content.strip().replace(" ", "")


def process_template_html(content: str, params: TemplateParams) -> str:
    """Обработка HTML: очистка, telnet-ссылки, копирование, обновление интерфейсов"""
    try:
        debug_log("Начало обработки HTML шаблона", params)

        # 1. Парсинг исходного HTML
        soup = BeautifulSoup(content, 'html.parser')
        if not soup:
            raise ValueError("Не удалось разобрать HTML")

        # 2. Очистка ненужных элементов
        for element in soup.find_all(True):
            if 'data-status' in element.attrs:
                del element['data-status']
            if 'onmousedown' in element.attrs:
                del element['onmousedown']
            if element.get('class') == ['hidden']:
                element.decompose()
            if element.name == 'i' and 'node_status' in element.get('class', []):
                element.decompose()

        # 3. Обработка telnet-ссылок
        if params.telnet_links:
            debug_log(f"Обработка telnet ссылок: {params.telnet_links}", params)
            for node in soup.find_all('div', class_='node'):
                node_name = node.get('data-name', '').strip()
                telnet_url = params.telnet_links.get(node_name)
                if not node_name or not telnet_url:
                    continue

                node['style'] = f"cursor: pointer; {node.get('style', '')}"
                node['onclick'] = f"window.open('{telnet_url}', '_blank')"

                if (icon := node.find('i', class_='nodehtmlconsole')):
                    icon['title'] = f"Telnet: {telnet_url.split('://')[-1].split('/')[0]}"

                if (name_div := node.find('div', class_='node_name')):
                    name_div['title'] = f"Подключиться: {telnet_url}"

        # 4. Обновление интерфейсов
        if params.interface_mapping:
            debug_log(f"Обновление интерфейсов: {params.interface_mapping}", params)

            iface_dict = {}
            for conn in params.interface_mapping:
                if len(conn) != 2:
                    continue
                devices = list(conn.items())
                src_node, src_iface = devices[0]
                dst_node, dst_iface = devices[1]
                key = frozenset((src_node, dst_node))
                iface_dict[key] = {src_node: src_iface, dst_node: dst_iface}

            for overlay_div in soup.find_all('div', class_='node_interface'):
                position = overlay_div.get('position')

                parent = overlay_div.find_parent('div', class_='jtk-overlay')
                if not parent:
                    continue

                class_list = parent.get('class', [])
                node_classes = [cls for cls in class_list if cls.startswith('node')]
                if len(node_classes) != 2:
                    continue

                name1 = node_classes[0]
                name2 = node_classes[1]

                # Найди реальные имена узлов
                node1_div = soup.find('div', class_=name1)
                node2_div = soup.find('div', class_=name2)
                if not node1_div or not node2_div:
                    continue

                real_name1 = node1_div.get('data-name')
                real_name2 = node2_div.get('data-name')
                if not real_name1 or not real_name2:
                    continue

                conn_key = frozenset((real_name1, real_name2))
                iface_pair = iface_dict.get(conn_key)
                if not iface_pair:
                    continue

                if position == 'src':
                    overlay_div.string = iface_pair.get(real_name1, '')
                elif position == 'dst':
                    overlay_div.string = iface_pair.get(real_name2, '')

        # 5. Создание контейнера
        container = BeautifulSoup(features='html.parser')
        custom_div = container.new_tag('div', id='customText1',
                                       **{
                                           'class': 'customShape customText context-menu ck-content jtk-draggable dragstopped ui-selectee',
                                           'data-path': '1',
                                           'style': 'position: absolute; display: block; top: 0px; left: 0px; width: 100%; height: 100vh; z-index: 1001;'
                                       })
        container.append(custom_div)

        # 6. Копирование узлов и соединений
        for node in soup.find_all('div', class_='node'):
            custom_div.append(node.__copy__())

        for connector in soup.find_all(class_=['jtk-connector', 'jtk-endpoint', 'jtk-overlay']):
            custom_div.append(connector.__copy__())

        return str(container)

    except Exception as e:
        debug_log(f"Критическая ошибка обработки: {str(e)}", params)
        raise ValueError(f"Ошибка обработки HTML: {str(e)}") from e


def generate_unl_from_template(
        template_path: str,
        lab_name: str,
        manual_url: str,
        telnet_links: Dict[str, str],
        interface_mapping: List[Dict[str, str]],
        output_dir: str = None,
        debug: bool = False
) -> bytes:
    """
    Генерация UNL файла из HTML шаблона

    Параметры:
        template_path (str): Путь к HTML шаблону
        lab_name (str): Название лабораторной работы (без расширения)
        manual_url (str): URL для сервиса методичек лаб
        telnet_links (Dict[str, str]): Словарь с telnet-ссылками в формате {имя_узла: url}
        interface_mapping (List[Dict[str, str]]): Список маппинга интерфейсов
        output_dir (str, optional): Директория для сохранения. По умолчанию - директория шаблона
        debug (bool, optional): Включить отладочный режим

    Возвращает:
        str: Путь к созданному UNL файлу
    """
    # Подготовка параметров
    template_path = Path(template_path)
    if not output_dir:
        output_dir = template_path.parent
    else:
        output_dir = Path(output_dir)

    params = TemplateParams(
        template_path=template_path,
        lab_name=lab_name,
        telnet_links=telnet_links,
        interface_mapping=interface_mapping,
        debug=debug
    )

    # Чтение и обработка шаблона
    html_content = template_path.read_text(encoding='utf-8')
    processed_html = process_template_html(html_content, params)
    base64_content = base64.b64encode(clean_html_content(processed_html).encode("utf-8")).decode()

    # Обработка ссылки методички
    iframe_workbook = create_iframe_workbooks(manual_url)

    # Сохранение UNL
    content = create_lab_xml(lab_name, base64_content, iframe_workbook)

    if debug:
        debug_html = output_dir / f"{lab_name}_debug.html"
        debug_html.write_text(processed_html, encoding='utf-8')
        print(f"Debug HTML saved to: {debug_html}")
        output_path = output_dir / f"{lab_name}.unl"
        output_path.write_bytes(content)

    return content


def debug_html_output(html_content: str, output_path: Path) -> None:
    """Сохранение отладочного HTML"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✓ Отладочный HTML сохранён: {output_path.resolve()}")
    except Exception as e:
        print(f"✖ Ошибка сохранения отладочного файла: {str(e)}")
