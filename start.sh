#!/bin/bash

set -e

echo "下载 Consul..."
CONSUL_VERSION="1.17.0"
curl -sL "https://releases.hashicorp.com/consul/${CONSUL_VERSION}/consul_${CONSUL_VERSION}_linux_amd64.zip" -o /tmp/consul.zip

echo "解压 Consul..."
unzip -o -q /tmp/consul.zip -d /usr/local/bin/
chmod +x /usr/local/bin/consul
rm /tmp/consul.zip

echo "Consul 版本:"
consul version

echo "启动应用..."
python app.py
