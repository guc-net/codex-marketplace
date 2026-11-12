FROM python:3.14-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends chromium fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
ENV GD_BROWSER=/usr/bin/chromium
