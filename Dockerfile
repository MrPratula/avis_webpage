FROM python:3.11-slim
LABEL authors="MrPratula"

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 443

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:433", "app:app"]
