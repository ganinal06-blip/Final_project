FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей для async drivers (если нужна)
RUN apt-get update && apt-get install -y build-essential

# Копируем только необходимые файлы
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "src.main"]