FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY hermes_runtime ./hermes_runtime

EXPOSE 8787

CMD ["python", "-m", "hermes_runtime"]
