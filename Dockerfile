FROM alpine:3.19

RUN apk add --no-cache curl ca-certificates tzdata

RUN curl -sL "https://releases.hashicorp.com/consul/1.17.0/consul_1.17.0_linux_amd64.zip" -o /tmp/consul.zip && \
    unzip -o -q /tmp/consul.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/consul && \
    rm /tmp/consul.zip

COPY zhub /app/zhub
COPY go/templates /app/templates
COPY go/static /app/static

RUN mkdir -p /app/data && \
    adduser -D -u 1000 -s /bin/sh appuser && \
    chown -R appuser:appuser /app

USER appuser

WORKDIR /app

EXPOSE 5000 8500

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/stats || exit 1

CMD ["sh", "-c", "/app/zhub & sleep 2 && consul agent -dev -ui -bind=0.0.0.0 -client=0.0.0.0 & wait"]
