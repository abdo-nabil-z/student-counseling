FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    gnupg \
    supervisor \
    libglib2.0-0 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libpangocairo-1.0-0 \
    libffi-dev \
    libharfbuzz-subset0 \
    shared-mime-info \
    fonts-dejavu \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

WORKDIR /workspace

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
