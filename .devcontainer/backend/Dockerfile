FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y \
    git \
    curl \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# FROM python:3.12-slim

# RUN apt-get update && apt-get install -y \
#     libglib2.0-0 \
#     libpango-1.0-0 \
#     libpangoft2-1.0-0 \
#     libharfbuzz0b \
#     libharfbuzz-subset0 \
#     libffi-dev \
#     shared-mime-info \
#     && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/backend

CMD ["sleep", "infinity"]
