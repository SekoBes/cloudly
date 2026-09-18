FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

WORKDIR /app

# Bu imajda chromium + tum sistem bagimliliklari zaten hazir geliyor
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV PORT=8000
EXPOSE 8000

CMD ["python", "app.py"]
