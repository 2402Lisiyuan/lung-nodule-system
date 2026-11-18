FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 直接复制当前目录下的 requirements.txt
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 复制当前目录所有代码
COPY . .

EXPOSE 8000

CMD uvicorn main:app --host 127.0.0.1 --port 8000