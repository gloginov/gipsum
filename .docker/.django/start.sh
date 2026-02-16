#!/bin/bash

echo "🚀 Запуск Gipsum E-commerce..."

# Проверка сети Traefik
if ! docker network ls | grep -q "${TRAEFIK_NETWORK_NAME}"; then
    echo "❌ Сеть ${TRAEFIK_NETWORK_NAME} не найдена. Создайте её:"
    echo "docker network create ${TRAEFIK_NETWORK_NAME}"
    exit 1
fi

# Создание директорий
mkdir -p data/db
mkdir -p data/media
mkdir -p frontend  # Пустая директория для фронтенда

# Права на директории
chmod -R 777 data

# Сборка и запуск
docker-compose up --build -d

echo "⏳ Ожидание запуска базы данных..."
sleep 5

# Создание суперпользователя (опционально)
echo "Создать суперпользователя? (y/n)"
read answer
if [ "$answer" = "y" ]; then
    docker-compose exec server-gipsum python manage.py createsuperuser
fi

echo "✅ Готово!"
echo "🌐 API: https://api-gipsum.docker"
echo "🌐 Frontend: https://gipsum.docker"
echo "⚙️  Admin: https://api-gipsum.docker/admin"