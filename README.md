# AI Chat
Чат с ИИ моделью

## Предварительные требования
- Docker (версия 20.10.0 или выше)
- Docker Compose (версия 1.29.0 или выше)
- Git (для клонирования репозитория)

## Установка и запуск
1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/ваш-username/ваш-репозиторий.git
   cd ваш-репозиторий

2. Создайте файл .env в корне проекта и заполните его:
   DB_NAME=your_db_name
   DB_USER=your_db_user
   DB_PASS=your_db_password
   RABBITMQ_USER=your_rabbit_user
   RABBITMQ_PASSWORD=your_rabbit_password

3. Запустите проект:
docker-compose up -d --build


## Сервисы будут доступны:
   Основное приложение: http://localhost
   RabbitMQ Management: http://localhost:15672
   ML Service: http://localhost:8000
   PostgreSQL: localhost:5432

## Остановка с сохранением данных:
docker-compose down

## Полная очистка (включая данные):
docker-compose down -v

## Структура сервисов
app - основное приложение
web-proxy - Nginx
rabbitmq - брокер сообщений
ml_service - сервис ML (Qwen/Qwen2-VL-2B-Instruct)
database - PostgreSQL

## Управление:
**Пересборка и перезапуск:**
docker-compose up -d --build

**Просмотр логов:**
docker-compose logs -f имя_сервиса

**Ресурсы**
ML Service: 4 CPU, 8GB RAM
RabbitMQ: 2GB дискового пространства
