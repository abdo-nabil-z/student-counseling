FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y \
    git curl ca-certificates gnupg supervisor \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

WORKDIR /workspace

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
