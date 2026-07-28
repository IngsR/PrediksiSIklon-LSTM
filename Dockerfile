# Gunakan image Python resmi yang ringan (disesuaikan dengan lingkungan lokal 3.13)
FROM python:3.13-slim

# Atur variabel lingkungan untuk mencegah Python menulis file .pyc dan buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Atur direktori kerja di dalam container
WORKDIR /app

# Instal dependensi sistem yang diperlukan
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Salin file requirements.txt terlebih dahulu untuk memanfaatkan layer caching Docker
COPY requirements.txt .

# Instal dependensi Python
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh isi proyek ke dalam direktori kerja
COPY . .

# Ekspos port default Streamlit
EXPOSE 8501

# Tambahkan Healthcheck untuk memastikan container berjalan dengan baik
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Perintah untuk menjalankan aplikasi
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
