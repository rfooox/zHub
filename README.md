# zHub - 资源导航与监控平台

简洁高效的内网/外网服务资源管理工具，支持 Consul 服务发现与同步。

## 功能特性

- **资源管理** - 添加、编辑、删除内外网服务资源
- **分类管理** - 支持按分类（内部服务、外部服务、数据库、中间件等）筛选
- **快速搜索** - 支持名称、地址、描述关键词搜索
- **状态监控** - 自动检测资源在线/离线状态，记录响应时间
- **Consul 集成** - 可选功能，支持：
  - 将资源同步到 Consul 进行服务注册
  - 从 Consul 导入已注册的服务
  - 自定义健康检查类型（HTTP/TCP）和检查间隔
  - 配置服务标签

## 技术栈

- **后端**: Python 3.10+ / Flask
- **数据库**: SQLite
- **Consul**: python-consul
- **前端**: 原生 HTML/CSS/JavaScript

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.yaml` 配置文件：

```yaml
app:
  host: 0.0.0.0
  port: 5000
  debug: true

consul:
  enabled: false        # 设为 true 启用 Consul 功能
  host: 127.0.0.1
  port: 8500
  datacenter: dc1
  scheme: http

health_check:
  enabled: true
  interval: 60         # 检查间隔（秒）
  timeout: 5           # 超时时间（秒）
```

### 3. 启动服务

```bash
python app.py
```

访问 http://localhost:5000

## 使用说明

### 添加资源

1. 点击右上角「添加资源」
2. 填写名称和地址（必填）
3. 选择分类和分组（可选）
4. 如需同步到 Consul，勾选「同步到 Consul」并配置检查参数
5. 点击保存

### Consul 同步

启用 Consul 功能后，可以：

- **同步到 Consul**：将本地资源配置注册到 Consul
- **导入 Consul**：从 Consul 导入已注册的服务列表

### 资源分类

| 分类 | 说明 |
|------|------|
| internal | 内部服务 |
| external | 外部服务 |
| database | 数据库 |
| middleware | 中间件 |
| monitoring | 监控服务 |
| consul | Consul 服务 |
| other | 其他 |

## 项目结构

```
├── app.py              # Flask 主应用
├── config.yaml         # 配置文件
├── models.py           # 数据模型
├── requirements.txt   # Python 依赖
├── routes/             # API 路由
│   ├── resources.py    # 资源管理
│   ├── consul.py       # Consul 集成
│   └── status.py       # 状态监控
├── services/            # 业务逻辑
│   ├── resource_service.py
│   ├── consul_service.py
│   ├── health_check.py
│   └── config_service.py
├── templates/           # HTML 模板
│   ├── index.html
│   ├── add.html
│   └── edit.html
└── static/             # 静态资源
    ├── css/style.css
    └── js/app.js
```

## API 接口

### 资源管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/resources | 获取资源列表 |
| GET | /api/resources/{id} | 获取单个资源 |
| POST | /api/resources | 添加资源 |
| PUT | /api/resources/{id} | 更新资源 |
| DELETE | /api/resources/{id} | 删除资源 |

### Consul 集成

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/consul/status | Consul 连接状态 |
| POST | /api/consul/sync-to-consul | 同步到 Consul |
| POST | /api/consul/sync-from-consul | 从 Consul 导入 |

### 状态监控

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/stats | 获取统计信息 |
| POST | /api/check/{id} | 手动检查状态 |

## License

MIT
