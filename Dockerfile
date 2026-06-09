FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

COPY src ./src
COPY vendor ./vendor

EXPOSE 8787

CMD ["python", "-m", "src.hermes"]
