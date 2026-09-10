# Container for Cloud Run. Gradio listens on 0.0.0.0:$PORT (Cloud Run sets $PORT).
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
EXPOSE 8080

CMD ["python", "app.py"]
