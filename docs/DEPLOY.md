# AgentOrchestrator 部署指南

## 环境要求

| 组件 | 最低版本 | 推荐版本 |
|------|---------|---------|
| Docker | 24.0 | 27.0+ |
| Docker Compose | 2.20 | 2.30+ |
| Python (本地开发) | 3.12 | 3.12+ |
| Java (本地开发) | 21 | 21 LTS |
| Maven (本地开发) | 3.9 | 3.9+ |
| PostgreSQL | 16 | 16 Alpine |
| Redis | 7 | 7 Alpine |

## 方式一：Docker Compose 部署 (推荐)

### 1. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

> 如果使用国内大模型 (DeepSeek/通义千问等)，修改 `OPENAI_BASE_URL` 和 `LLM_MODEL` 即可。

### 2. 启动所有服务

```bash
docker compose up -d
```

### 3. 查看日志

```bash
# 所有服务
docker compose logs -f

# 只看 Agent Core
docker compose logs -f agent-core

# 只看管理后台
docker compose logs -f admin-server
```

### 4. 验证部署

```bash
curl http://localhost:8000/health
# {"status":"ok","app":"AgentOrchestrator","version":"0.1.0",...}

curl http://localhost:9090/api/admin/health
# {"admin_server":"ok","agent_core":{"status":"ok",...}}
```

### 5. 停止服务

```bash
docker compose down           # 保留数据卷
docker compose down -v        # 删除数据卷
```

---

## 方式二：本地开发部署

### Python Agent Core

```bash
cd agent-core

# 使用清华镜像
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 创建虚拟环境
python -m venv venv
source venv/bin/activate       # Linux/macOS
# venv\Scripts\activate        # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export OPENAI_API_KEY=sk-your-key
export LLM_MODEL=gpt-4o

# 启动 (开发模式，自动重载)
python main.py
# 或
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Java Admin Server

```bash
cd admin-server

# 使用阿里云 Maven 镜像 (国内推荐)
# 编辑 ~/.m2/settings.xml 添加 mirror

# 启动
./mvnw spring-boot:run

# 或打包后运行
./mvnw package -DskipTests
java -jar target/admin-server-0.1.0.jar
```

### 数据库

需要本地运行 PostgreSQL 和 Redis：

```bash
# Docker 单独启动数据库
docker run -d --name ao-pg \
  -e POSTGRES_DB=agent_orchestrator \
  -e POSTGRES_USER=ao_user \
  -e POSTGRES_PASSWORD=ao_pass_2026 \
  -p 5432:5432 postgres:16-alpine

docker run -d --name ao-redis -p 6379:6379 redis:7-alpine
```

---

## 方式三：生产环境 (Kubernetes)

```yaml
# 简化示例，完整配置按需调整
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-core
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: agent-core
        image: your-registry/agent-core:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: ao-secrets
              key: openai-api-key
---
apiVersion: v1
kind: Service
metadata:
  name: agent-core
spec:
  ports:
  - port: 8000
  selector:
    app: agent-core
```

---

## 国内镜像加速

### Docker 镜像加速

编辑 `/etc/docker/daemon.json`：

```json
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me"
  ]
}
```

### pip 镜像

```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### Maven 镜像

编辑 `~/.m2/settings.xml`：

```xml
<mirrors>
  <mirror>
    <id>aliyun</id>
    <mirrorOf>central</mirrorOf>
    <url>https://maven.aliyun.com/repository/public</url>
  </mirror>
</mirrors>
```
