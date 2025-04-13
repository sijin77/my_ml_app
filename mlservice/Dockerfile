# Базовый образ Python 3.10
FROM python:3.10-slim

# 2. Рабочая директория
WORKDIR /app

# 3. Копируем файл зависимостей
COPY requirements.txt /app/

# 4. Установка Python-зависимостей
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

CMD [ "python", "main.py"]