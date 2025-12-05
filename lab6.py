import os
import logging
from functools import wraps
import xml.etree.ElementTree as ET


# Користувацькі винятки
class FileNotFoundError(Exception):
    """Виняток, коли файл не знайдено"""
    def __init__(self, filepath):
        super().__init__(f"Файл не знайдено: {filepath}")


class FileCorruptedError(Exception):
    """Виняток, коли файл пошкоджено або неможливо виконати операцію"""
    def __init__(self, filepath, reason=""):
        msg = f"Файл пошкоджено: {filepath}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)


# Декоратор для логування
def logged(exception_type, mode="console"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__name__)
            logger.setLevel(logging.INFO)
            logger.handlers.clear()
            
            handler = logging.StreamHandler() if mode == "console" else logging.FileHandler("file_operations.log", encoding='utf-8')
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            
            try:
                logger.info(f"Виклик {func.__name__}")
                result = func(*args, **kwargs)
                logger.info(f"{func.__name__} виконано успішно")
                return result
            except exception_type as e:
                logger.error(f"{exception_type.__name__}: {e}")
                raise
            finally:
                handler.close()
                logger.removeHandler(handler)
        return wrapper
    return decorator


class XMLFileHandler:
    """Клас для роботи з XML файлами"""
    
    def __init__(self, filepath):
        self.filepath = filepath
        if not os.path.exists(filepath):
            raise FileNotFoundError(filepath)
    
    @logged(FileCorruptedError, mode="console")
    def read(self):
        try:
            return ET.parse(self.filepath).getroot()
        except ET.ParseError as e:
            raise FileCorruptedError(self.filepath, f"XML помилка: {e}")
        except PermissionError:
            raise FileCorruptedError(self.filepath, "Немає прав для читання")
        except Exception as e:
            raise FileCorruptedError(self.filepath, str(e))
    
    @logged(FileCorruptedError, mode="file")
    def write(self, root):
        try:
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ")
            tree.write(self.filepath, encoding='utf-8', xml_declaration=True)
        except PermissionError:
            raise FileCorruptedError(self.filepath, "Немає прав для запису")
        except Exception as e:
            raise FileCorruptedError(self.filepath, str(e))
    
    @logged(FileCorruptedError, mode="file")
    def append(self, new_element):
        try:
            tree = ET.parse(self.filepath)
            tree.getroot().append(new_element)
            ET.indent(tree, space="  ")
            tree.write(self.filepath, encoding='utf-8', xml_declaration=True)
        except ET.ParseError as e:
            raise FileCorruptedError(self.filepath, f"XML помилка: {e}")
        except PermissionError:
            raise FileCorruptedError(self.filepath, "Немає прав")
        except Exception as e:
            raise FileCorruptedError(self.filepath, str(e))


# Демонстрація
if __name__ == "__main__":
    print("Запуск \n")
    
    # Перевіряємо, чи це перший чи другий запуск
    if not os.path.exists("file_operations.log"):
        # ПЕРШИЙ ЗАПУСК - створюємо лог файл
        print(" Спроба відкрити неіснуючий 'demo.xml':")
        try:
            handler = XMLFileHandler("demo.xml")
        except FileNotFoundError as e:
            print(f" ! {e}")
        
        print("\n Створюємо лог файл через декоратор...")
        # Створимо тимчасовий файл щоб спрацював декоратор з mode="file"
        temp_root = ET.Element("temp")
        temp_tree = ET.ElementTree(temp_root)
        temp_tree.write("temp.xml", encoding='utf-8', xml_declaration=True)
        
        temp_handler = XMLFileHandler("temp.xml")
        temp_handler.write(temp_root)  # Це створить file_operations.log
        
        os.remove("temp.xml")
        print("Файл 'file_operations.log' створено")
        
    
    else:
        # ДРУГИЙ ЗАПУСК - створюємо demo.xml
        print("1. Створюємо 'demo.xml':")
        root = ET.Element("data")
        ET.SubElement(root, "item", id="1").text = "Перший елемент"
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write("demo.xml", encoding='utf-8', xml_declaration=True)
        print("Файл 'demo.xml' створено")
        
        print("\n Відкриваємо 'demo.xml':")
        handler = XMLFileHandler("demo.xml")
        print("Файл відкрито")
        
        print("\n Читаємо файл:")
        root = handler.read()
        for child in root:
            print(f"   - <{child.tag} id='{child.get('id')}'>{child.text}</{child.tag}>")
        
        print("\n Додаємо елемент:")
        new_item = ET.Element("item", id="2")
        new_item.text = "Другий елемент"
        handler.append(new_item)
        print("Елемент додано")
        
        print("\n5. Читаємо оновлений файл:")
        root = handler.read()
        for child in root:
            print(f"   - <{child.tag} id='{child.get('id')}'>{child.text}</{child.tag}>")
        
        print("\n Перезаписуємо файл:")
        new_root = ET.Element("data")
        ET.SubElement(new_root, "item", id="100").text = "Новий вміст"
        handler.write(new_root)
        print("Файл перезаписано")
        
        print("\n7. Читаємо перезаписаний файл:")
        root = handler.read()
        for child in root:
            print(f"   - <{child.tag} id='{child.get('id')}'>{child.text}</{child.tag}>")
        


# with open("demo.xml", "w", encoding='utf-8') as f:
#     f.write("<?xml version='1.0'?><data><item>Незакритий тег")
# 
# print("\n8. Спроба прочитати пошкоджений 'demo.xml':")
# try:
#     handler.read()
# except FileCorruptedError as e:
#     print(f" {e}")
        
