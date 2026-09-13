FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -fsSL --retry 5 --retry-delay 2 \
         -o /usr/local/bin/cloudflared \
         https://github.com/cloudflare/cloudflared/releases/download/2025.2.1/cloudflared-linux-amd64 \
    && chmod +x /usr/local/bin/cloudflared \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
COPY keeper.py /keeper.py

ENV QP_ORIGIN_URL=http://miniapp:80
ENV ENV_FILE=/work/.env
ENV URL_FILE=/work/miniapp_url.txt

CMD ["python", "-u", "/keeper.py"]
