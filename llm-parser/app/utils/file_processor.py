import json
from typing import Any, Dict
import mimetypes
import logging

logger = logging.getLogger(__name__)


class FileProcessor:
    """Обработчик файлов по типу"""

    @staticmethod
    def process_file_by_type(file_bytes: bytes, content_type: str = None, filename: str = None) -> Dict[str, Any]:
        """
        Преобразует байты файла в зависимости от типа

        :param file_bytes: Байты файла
        :param content_type: MIME тип (если известен)
        :param filename: Имя файла (для определения типа по расширению)
        :return: Словарь с результатом обработки
        """
        # Определяем тип файла
        if not content_type:
            if filename:
                content_type = mimetypes.guess_type(filename)[0]
            else:
                content_type = 'application/octet-stream'

        # Обработка в зависимости от типа
        try:
            if content_type == 'application/json':
                return FileProcessor._process_json(file_bytes)

            elif content_type in ['application/pdf', 'application/x-pdf']:
                return FileProcessor._process_pdf(file_bytes)

            elif content_type.startswith('image/'):
                return FileProcessor._process_image(file_bytes, content_type)

            elif content_type in ['text/plain', 'text/csv']:
                return FileProcessor._process_text(file_bytes)

            elif content_type in ['application/vnd.ms-excel',
                                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                return FileProcessor._process_excel(file_bytes)

            elif content_type in ['application/msword',
                                  'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                return FileProcessor._process_word(file_bytes)

            else:
                return FileProcessor._process_generic(file_bytes, content_type)

        except Exception as e:
            logger.error(f"Ошибка обработки файла типа {content_type}: {e}")
            raise e

    @staticmethod
    def _process_json(file_bytes: bytes) -> Dict[str, Any]:
        """Обработка JSON файла"""
        try:
            data = json.loads(file_bytes.decode('utf-8'))
            return {
                'type': 'json',
                'data': data,
                'size': len(file_bytes)
            }
        except json.JSONDecodeError as e:
            raise ValueError(f"Некорректный JSON: {e}")

    @staticmethod
    def _process_pdf(file_bytes: bytes) -> Dict[str, Any]:
        """Обработка PDF файла - извлечение текста"""
        try:
            from PyPDF2 import PdfReader
            import io

            pdf_file = io.BytesIO(file_bytes)
            reader = PdfReader(pdf_file)

            # Извлекаем текст со всех страниц
            text_pages = []
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    text_pages.append({
                        'page': page_num + 1,
                        'text': text
                    })

            return {
                'type': 'pdf',
                'pages_count': len(reader.pages),
                'pages': text_pages,
                'size': len(file_bytes),
                'has_text': len(text_pages) > 0
            }
        except ImportError:
            raise ImportError("Требуется установка: pip install PyPDF2")
        except Exception as e:
            raise ValueError(f"Ошибка обработки PDF: {e}")

    @staticmethod
    def _process_image(file_bytes: bytes, content_type: str) -> Dict[str, Any]:
        """Обработка изображения"""
        try:
            from PIL import Image
            import io

            img_file = io.BytesIO(file_bytes)
            img = Image.open(img_file)

            return {
                'type': 'image',
                'format': img.format,
                'content_type': content_type,
                'size': len(file_bytes),
                'dimensions': {
                    'width': img.width,
                    'height': img.height
                },
                'mode': img.mode
            }
        except ImportError:
            raise ImportError("Требуется установка: pip install Pillow")
        except Exception as e:
            raise ValueError(f"Ошибка обработки изображения: {e}")

    @staticmethod
    def _process_text(file_bytes: bytes) -> Dict[str, Any]:
        """Обработка текстового файла"""
        try:
            text = file_bytes.decode('utf-8')
            return {
                'type': 'text',
                'content': text,
                'lines_count': len(text.split('\n')),
                'size': len(file_bytes)
            }
        except UnicodeDecodeError:
            # Попробуем другую кодировку
            text = file_bytes.decode('cp1251', errors='ignore')
            return {
                'type': 'text',
                'content': text,
                'encoding': 'cp1251',
                'lines_count': len(text.split('\n')),
                'size': len(file_bytes)
            }

    @staticmethod
    def _process_excel(file_bytes: bytes) -> Dict[str, Any]:
        """Обработка Excel файла"""
        try:
            import pandas as pd
            import io

            excel_file = io.BytesIO(file_bytes)

            # Читаем все листы
            sheets = pd.read_excel(excel_file, sheet_name=None)

            sheets_info = {}
            for sheet_name, df in sheets.items():
                sheets_info[sheet_name] = {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'column_names': df.columns.tolist()
                }

            return {
                'type': 'excel',
                'sheets_count': len(sheets),
                'sheets': sheets_info,
                'size': len(file_bytes)
            }
        except ImportError:
            raise ImportError("Требуется установка: pip install pandas openpyxl")
        except Exception as e:
            raise ValueError(f"Ошибка обработки Excel: {e}")

    @staticmethod
    def _process_word(file_bytes: bytes) -> Dict[str, Any]:
        """Обработка Word документа"""
        try:
            from docx import Document
            import io

            doc_file = io.BytesIO(file_bytes)
            doc = Document(doc_file)

            # Извлекаем текст
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

            return {
                'type': 'word',
                'paragraphs_count': len(paragraphs),
                'paragraphs': paragraphs[:10],  # Первые 10 параграфов
                'has_more': len(paragraphs) > 10,
                'size': len(file_bytes)
            }
        except ImportError:
            raise ImportError("Требуется установка: pip install python-docx")
        except Exception as e:
            raise ValueError(f"Ошибка обработки Word: {e}")

    @staticmethod
    def _process_generic(file_bytes: bytes, content_type: str) -> Dict[str, Any]:
        """Обработка неизвестного типа файла"""
        return {
            'type': 'generic',
            'content_type': content_type,
            'size': len(file_bytes),
            'data': file_bytes  # Возвращаем сырые байты
        }