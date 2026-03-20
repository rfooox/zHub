FROM python:3.11-alpine AS builder

WORKDIR /app

RUN apk add --no-cache gcc musl-dev

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM alpine:3.19

RUN apk add --no-cache curl

COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

RUN adduser -D -u 1000 appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app

RUN curl -sL "https://releases.hashicorp.com/consul/1.17.0/consul_1.17.0_linux_amd64.zip" -o /tmp/consul.zip && \
    unzip -o -q /tmp/consul.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/consul && \
    rm /tmp/consul.zip && \
    adduser -D -u 1000 -s /bin/sh appuser

USER appuser

WORKDIR /app

EXPOSE 5000 8500

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/stats || exit 1

CMD ["sh", "-c", "consul agent -dev -ui -bind=0.0.0.0 -client=0.0.0.0 & sleep 2 && python app.py"]
