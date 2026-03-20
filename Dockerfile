FROM python:3.11-slim

ENV APP_HOME=/app
WORKDIR $APP_HOME

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sL "https://releases.hashicorp.com/consul/1.17.0/consul_1.17.0_linux_amd64.zip" -o /tmp/consul.zip && \
    unzip -o -q /tmp/consul.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/consul && \
    rm /tmp/consul.zip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data && chown -R 1000:1000 data

USER 1000

EXPOSE 5000 8500

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/stats || exit 1

CMD ["sh", "-c", "consul agent -dev -ui -bind=0.0.0.0 -client=0.0.0.0 & sleep 2 && python app.py"]
