FROM node:20-bullseye-slim

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# No global scaffold tool needed — Vite projects are created with:
#   npm create vite@latest .
# Vite itself is installed as a local dev dependency inside the project.

WORKDIR /workspace/frontend

CMD ["sleep", "infinity"]
