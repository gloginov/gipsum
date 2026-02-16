import os
import re
import json
import pandas as pd
import requests
from io import BytesIO
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from .models import Product, Category, ProductImage
from .import_models import ProductImport, ProductImportLog


class ProductImportService:
    """Сервис импорта товаров из Excel/CSV"""
    
    BOOLEAN_TRUE = ['true', '1', 'yes', 'да', 'д', 'y', '+', 'on', 'вкл', 'да']
    
    def __init__(self, import_task: ProductImport):
        self.task = import_task
        self.errors = []
    
    def process(self):
        """Основной метод обработки"""
        self.task.status = 'processing'
        self.task.save()
        
        try:
            # Читаем файл
            df = self._read_file()
            self.task.total_rows = len(df)
            self.task.save()
            
            # Обрабатываем каждую строку
            for idx, row in df.iterrows():
                row_num = int(idx) + 2  # +2: заголовок и 0-based индекс
                try:
                    self._process_row(row, row_num)
                except Exception as e:
                    self._log(row_num, row, 'error', str(e))
                    self.task.error_count += 1
            
            # Определяем финальный статус
            if self.task.error_count == 0:
                self.task.status = 'completed'
            elif self.task.created_count > 0 or self.task.updated_count > 0:
                self.task.status = 'partial'
            else:
                self.task.status = 'error'
                
        except Exception as e:
            self.task.status = 'error'
            self.task.error_message = str(e)
        
        from django.utils import timezone
        self.task.processed_at = timezone.now()
        self.task.save()
        
        # Генерируем лог
        self._generate_log_file()
    
    def _read_file(self) -> pd.DataFrame:
        """Чтение файла"""
        path = self.task.file.path
        ext = os.path.splitext(path)[1].lower()
        
        if ext == '.csv':
            # Пробуем разные кодировки
            for encoding in ['utf-8', 'utf-8-sig', 'cp1251', 'latin1']:
                try:
                    return pd.read_csv(path, encoding=encoding, dtype=str)
                except:
                    continue
            raise ValueError("Не удалось прочитать CSV файл")
        
        elif ext in ['.xlsx', '.xls']:
            return pd.read_excel(path, dtype=str)
        
        else:
            raise ValueError(f"Неподдерживаемый формат: {ext}")
    
    def _process_row(self, row: pd.Series, row_num: int):
        """Обработка одной строки"""
        # Преобразуем в словарь, убираем NaN
        data = {}
        for key, val in row.items():
            if pd.notna(val):
                data[str(key).strip().lower()] = str(val).strip()
        
        # Проверяем обязательные поля
        name = data.get('name')
        price = data.get('price')
        
        if not name:
            self._log(row_num, data, 'error', 'Отсутствует обязательное поле: name')
            return
        
        if not price:
            self._log(row_num, data, 'error', 'Отсутствует обязательное поле: price')
            return
        
        # Ищем существующий товар по SKU
        sku = data.get('sku')
        existing = None
        
        if sku:
            existing = Product.objects.filter(sku=sku).first()
        
        # Определяем действие
        if existing:
            if self.task.import_type == 'create':
                self._log(row_num, data, 'skipped', f'Товар с SKU {sku} уже существует')
                self.task.skipped_count += 1
                return
            self._update_product(existing, data, row_num)
        else:
            if self.task.import_type == 'update':
                self._log(row_num, data, 'skipped', f'Товар с SKU {sku} не найден')
                self.task.skipped_count += 1
                return
            self._create_product(data, row_num)
    
    def _create_product(self, data: dict, row_num: int):
        """Создание товара"""
        try:
            with transaction.atomic():
                product = Product.objects.create(
                    name=data['name'],
                    slug=data.get('slug') or slugify(data['name'], allow_unicode=True),
                    sku=data.get('sku') or self._generate_sku(),
                    description=data.get('description', ''),
                    short_description=data.get('short_description', ''),
                    price=self._to_decimal(data['price']) or Decimal('0'),
                    old_price=self._to_decimal(data.get('old_price')),
                    stock=self._to_int(data.get('stock')) or 0,
                    is_available=self._to_bool(data.get('is_available', 'true')),
                    is_featured=self._to_bool(data.get('is_featured')),
                    is_new=self._to_bool(data.get('is_new')),
                    is_bestseller=self._to_bool(data.get('is_bestseller')),
                )
                
                # Категории
                if data.get('categories'):
                    cats = self._parse_categories(data['categories'])
                    product.categories.set(cats)
                    if cats:
                        product.main_category = cats[0]
                        product.save()
                elif self.task.default_category:
                    product.categories.add(self.task.default_category)
                    product.main_category = self.task.default_category
                    product.save()
                
                # Изображения
                self._process_images(product, data)
                
                self.task.created_count += 1
                self._log(row_num, data, 'created', f'Товар создан: {product.name} (ID: {product.id})')
                
        except Exception as e:
            self._log(row_num, data, 'error', f'Ошибка создания: {str(e)}')
            self.task.error_count += 1
    
    def _update_product(self, product: Product, data: dict, row_num: int):
        """Обновление товара"""
        try:
            with transaction.atomic():
                # Обновляем поля
                if data.get('name'):
                    product.name = data['name']
                if data.get('slug'):
                    product.slug = data['slug']
                
                price = self._to_decimal(data.get('price'))
                if price is not None:
                    product.price = price
                
                old_price = self._to_decimal(data.get('old_price'))
                if old_price is not None:
                    product.old_price = old_price
                
                stock = self._to_int(data.get('stock'))
                if stock is not None:
                    product.stock = stock
                
                # Булевы поля
                if 'is_available' in data:
                    product.is_available = self._to_bool(data['is_available'])
                if 'is_featured' in data:
                    product.is_featured = self._to_bool(data['is_featured'])
                if 'is_new' in data:
                    product.is_new = self._to_bool(data['is_new'])
                if 'is_bestseller' in data:
                    product.is_bestseller = self._to_bool(data['is_bestseller'])
                
                product.save()
                
                # Обновляем категории если указаны
                if data.get('categories'):
                    cats = self._parse_categories(data['categories'])
                    product.categories.set(cats)
                
                # Обновляем изображения если разрешено
                if self.task.update_images:
                    product.images.all().delete()
                    self._process_images(product, data)
                
                self.task.updated_count += 1
                self._log(row_num, data, 'updated', f'Товар обновлен: {product.name}')
                
        except Exception as e:
            self._log(row_num, data, 'error', f'Ошибка обновления: {str(e)}')
            self.task.error_count += 1
    
    def _parse_categories(self, categories_str: str) -> list:
        """Парсинг строки категорий"""
        if not categories_str:
            return []
        
        result = []
        for cat_name in categories_str.split(','):
            cat_name = cat_name.strip()
            if not cat_name:
                continue
            
            # Создаем или находим категорию
            slug = slugify(cat_name, allow_unicode=True)
            cat, _ = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': cat_name, 'is_active': True}
            )
            result.append(cat)
        
        return result
    
    def _process_images(self, product: Product, data: dict):
        """Обработка изображений"""
        images = []
        
        for i in range(1, 6):
            url = data.get(f'image_{i}')
            if url:
                images.append({
                    'url': url,
                    'is_main': i == 1,
                    'order': i
                })
        
        for img_data in images:
            try:
                self._download_image(product, img_data)
            except Exception as e:
                print(f"Error image {img_data['url']}: {e}")
    
    def _download_image(self, product: Product, img_data: dict):
        """Скачивание изображения"""
        url = img_data['url']
        
        # Пропускаем пустые URL
        if not url or url.lower() in ['nan', 'none', 'null', '-']:
            return
        
        # Если локальный путь
        if url.startswith('/media/'):
            path = url.replace('/media/', '')
            if default_storage.exists(path):
                ProductImage.objects.create(
                    product=product,
                    image=path,
                    is_main=img_data['is_main'],
                    order=img_data['order']
                )
            return
        
        # Скачиваем по URL
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            ext = url.split('.')[-1].split('?')[0][:4]
            if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                ext = 'jpg'
            
            filename = f"{slugify(product.name)[:30]}_{img_data['order']}.{ext}"
            
            ProductImage.objects.create(
                product=product,
                image=ContentFile(response.content, name=filename),
                is_main=img_data['is_main'],
                order=img_data['order']
            )
        except Exception as e:
            raise Exception(f"Download failed: {e}")
    
    def _to_decimal(self, val) -> Decimal | None:
        """Конвертация в Decimal"""
        if not val or str(val).lower() in ['nan', 'none', 'null', '']:
            return None
        try:
            cleaned = str(val).replace(',', '.').replace(' ', '').replace('₽', '').replace('$', '')
            return Decimal(cleaned)
        except:
            return None
    
    def _to_int(self, val) -> int | None:
        """Конвертация в int"""
        if not val or str(val).lower() in ['nan', 'none', 'null', '']:
            return None
        try:
            return int(float(str(val).replace(',', '.')))
        except:
            return None
    
    def _to_bool(self, val) -> bool:
        """Конвертация в bool"""
        if not val:
            return False
        return str(val).lower() in self.BOOLEAN_TRUE
    
    def _generate_sku(self) -> str:
        """Генерация SKU"""
        from datetime import datetime
        import random
        return f"SKU-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
    
    def _log(self, row_num: int, data: dict, status: str, message: str):
        """Создание лога"""
        ProductImportLog.objects.create(
            import_task=self.task,
            row_number=row_num,
            sku=str(data.get('sku', '')),
            product_name=str(data.get('name', '')),
            status=status,
            message=message,
            raw_data=data
        )
    
    def _generate_log_file(self):
        """Генерация CSV лога"""
        import csv
        
        logs = self.task.logs.all()
        if not logs:
            return
        
        output = []
        writer = csv.writer(output)
        writer.writerow(['Row', 'SKU', 'Name', 'Status', 'Message'])
        
        for log in logs:
            writer.writerow([
                log.row_number,
                log.sku,
                log.product_name,
                log.status,
                log.message
            ])
        
        filename = f'import_{self.task.id}_log.csv'
        self.task.log_file.save(
            filename,
            ContentFile('\n'.join(output).encode('utf-8-sig'))
        )