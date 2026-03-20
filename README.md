# zHub - 资源导航与监控平台

简洁高效的内网/外网服务资源管理工具，支持 Consul 服务发现与同步。

## 功能特性

- **资源管理** - 添加、编辑、删除内外网服务资源
- **分类管理** - 支持按分类（内部服务、外部服务、数据库、中间件等）筛选
- **快速搜索** - 支持名称、地址、描述关键词搜索
- **状态监控** - 自动检测资源在线/离线状态，记录响应时间
- **Consul 集成** - 可选功能，支持服务注册与发现

## 技术栈

- **后端**: Go 1.21 / Gin
- **数据库**: SQLite
- **Consul**: HashiCorp Consul
- **前端**: 原生 HTML/CSS/JavaScript

## 快速开始

### 1. 安装依赖

```bash
go mod download
```

### 2. 配置

环境变量配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `APP_HOST` | 0.0.0.0 | 服务地址 |
| `APP_PORT` | 5000 | 服务端口 |
| `CONSUL_ENABLED` | true | 启用 Consul |
| `CONSUL_HOST` | 127.0.0.1 | Consul 地址 |
| `CONSUL_PORT` | 8500 | Consul 端口 |
| `HEALTH_CHECK_ENABLED` | true | 启用健康检查 |
| `HEALTH_CHECK_INTERVAL` | 60 | 检查间隔（秒） |
| `HEALTH_CHECK_TIMEOUT` | 5 | 超时时间（秒） |

### 3. 启动服务

```bash
go run ./cmd
```

访问 http://localhost:5000

## 使用 Docker 部署

### 构建镜像

```bash
docker build -t zhub .
```

### 运行容器

```bash
docker run -d -p 5000:5000 -p 8500:8500 --name zhub zhub
```

### 使用 docker-compose

```bash
docker-compose up -d
```

## 项目结构

```
├── go/
│   ├── cmd/
│   │   └── main.go           # 程序入口
│   ├── internal/
│   │   ├── config/          # 配置管理
│   │   ├── models/          # 数据模型
│   │   └── routes/          # 路由处理
│   ├── templates/           # HTML 模板
│   ├── static/              # 静态资源
│   └── go.mod               # Go 模块
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## API 接口

### 资源管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/resources | 获取资源列表 |
| GET | /api/resources/:id | 获取单个资源 |
| POST | /api/resources | 添加资源 |
| PUT | /api/resources/:id | 更新资源 |
| DELETE | /api/resources/:id | 删除资源 |

### Consul 集成

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/consul/status | Consul 状态 |
| POST | /api/consul/sync-to-consul | 同步到 Consul |
| POST | /api/consul/sync-from-consul | 从 Consul 导入 |

### 状态监控

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/stats | 获取统计信息 |
| POST | /api/check/:id | 手动检查状态 |

## License

MIT
