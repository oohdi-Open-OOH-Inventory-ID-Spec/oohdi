FROM python:3.12-slim

WORKDIR /app

COPY website /app/website
COPY img /app/img

RUN pip install --no-cache-dir dnspython

EXPOSE 8080

CMD ["python", "/app/website/app.py"]
