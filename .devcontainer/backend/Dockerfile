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



WORKDIR /workspace/backend

CMD ["sleep", "infinity"]
