import xml.etree.ElementTree as ET
import os

XML_FILE = "data/products.xml"


def _ensure_dir():
    os.makedirs("data", exist_ok=True)


def save_products_xml(products: list):
    _ensure_dir()
    root = ET.Element("products")

    for p in products:
        d = p.to_dict()
        prod_el = ET.SubElement(root, "product")
        for key, value in d.items():
            child = ET.SubElement(prod_el, key)
            child.text = str(value)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")          # pretty-print (Python 3.9+)
    tree.write(XML_FILE, encoding="unicode", xml_declaration=True)
    print(f"  ✅ XML saved     → {XML_FILE}")


def load_products_xml() -> list:
    if not os.path.exists(XML_FILE):
        return []
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    products_data = []
    for prod_el in root.findall("product"):
        d = {child.tag: child.text for child in prod_el}
        products_data.append(d)
    return products_data
