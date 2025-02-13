FROM python:3.11-slim
LABEL authors="MrPratula"

WORKDIR /app
COPY . .
COPY config/cert.pem /etc/ssl/certs/cert.pem
COPY config/key.pem /etc/ssl/private/key.pem
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 443

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:443", "--certfile=/etc/ssl/certs/cert.pem", "--keyfile=/etc/ssl/private/key.pem", "app:app"]
