FROM python:3.11-slim

WORKDIR /app

# Sistem bagimliliklarini playwright kendi kuracak (install-deps),
# once pip paketlerini kuruyoruz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright chromium + gerekli sistem kutuphanelerini kur
RUN playwright install --with-deps chromium

COPY app.py .

# Render, PORT env variable'ini kendisi verir
ENV PORT=8000
EXPOSE 8000

CMD ["python", "app.py"]
