FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıklarını yükle
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıklarını yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# Port
EXPOSE 8501

# Streamlit yapılandırması
RUN mkdir -p /root/.streamlit
RUN echo "[server]\nheadless = true\nport = 8501\naddress = \"0.0.0.0\"" > /root/.streamlit/config.toml

# Uygulamayı başlat
CMD ["streamlit", "run", "app.py"]
