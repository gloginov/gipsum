FROM python:3.11-slim

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /code

# Копирование requirements и установка зависимостей
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта (для production, для dev используется volume)
COPY backend/ .

# Создание директории для медиа
RUN mkdir -p media

EXPOSE 5000

CMD ["python", "manage.py", "runserver", "0.0.0.0:5000"]