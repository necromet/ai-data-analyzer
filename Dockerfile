# syntax=docker/dockerfile:1

# This Dockerfile builds the backend/API container only.
ARG PYTHON_VERSION=3.12.3
FROM python:${PYTHON_VERSION}-slim

# Prevent Python from writing pyc files and buffering logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# install python dependencies
COPY langgraph_app/pyproject.toml langgraph_app/Makefile langgraph_app/ /app/langgraph_app/
COPY db_api_requirements.txt /app/

# install postgres client utilities so we can wait for the server to become ready
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client && \
    rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/db_api_requirements.txt && \
    pip install --no-cache-dir /app/langgraph_app && \
    rm -rf /root/.cache/pip

# copy source code and expose the API port
COPY . .
EXPOSE 8000

# start the backend server
CMD ["python", "db_api_server.py"]
