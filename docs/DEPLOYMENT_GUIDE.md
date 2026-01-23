# 部署指南

本指南涵盖Web Dashboard的使用、局域网访问等所有部署相关内容。

---

## 📑 目录

1. [Web Dashboard使用](#web-dashboard使用)
2. [局域网访问](#局域网访问)

4. [生产环境部署](#生产环境部署)

---

# Web Dashboard使用

## 🌐 Web可视化界面

### 功能特点

- 📊 **实时统计卡片** - 总代理数、活跃数、成功率
- 📈 **交互式图表** - 国家分布、代理源状态
- 📋 **代理列表** - 可搜索、排序、查看详情
- 🌙 **现代化界面** - 深色主题、响应式设计

### 界面预览

```
┌─────────────────────────────────────────────────┐
│  🌐 SOCKS5代理池监控    [🔄 刷新] [⬇️ 导出]   │
├─────────────────────────────────────────────────┤
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐                  │
│  │📊  │ │✅  │ │🎯  │ │🔍  │                  │
│  │523 │ │312 │ │68% │ │1245│                  │
│  └────┘ └────┘ └────┘ └────┘                  │
│                                                 │
│  ┌──────────┐  ┌──────────┐                   │
│  │ 国家分布 │  │ 代理源   │                   │
│  │ (饼图)   │  │ (柱状图) │                   │
│  └──────────┘  └──────────┘                   │
│                                                 │
│  🔍 [搜索...]  [国家筛选▼]                     │
│  代理列表 (可排序、点击查看详情)               │
└─────────────────────────────────────────────────┘
```

## 🚀 快速启动

### 本地访问

```bash
# 启动Dashboard
python web_dashboard.py

# 访问
http://localhost:5000
```

### API端点

```bash
# 获取统计
GET /api/stats

# 获取代理列表
GET /api/proxies?limit=10

# 获取单个代理详情
GET /api/proxy/1.2.3.4:1080

# 导出代理
GET /api/export?format=json  # 或 txt, csv
```

---

# 局域网访问

## 📱 在手机/平板上访问

### 特点

- ✅ 已配置为 `host='0.0.0.0'`
- ✅ 支持同WiFi下所有设备访问
- ✅ 响应式设计，自动适配移动端

### 使用步骤

#### 1. 启动Dashboard

```bash
python web_dashboard.py
```

会显示:
```
============================================================
Web Dashboard 启动成功！
============================================================
本地访问: http://localhost:5000
局域网访问: http://你的IP地址:5000
============================================================
```

#### 2. 查看IP地址

**Windows:**
```bash
ipconfig
```

找到 "IPv4 地址"，例如: `192.168.1.100`

**Linux/Mac:**
```bash
ifconfig
# 或
ip addr
```

#### 3. 移动设备访问

1. **确保在同一WiFi**
2. **打开浏览器**
3. **输入地址**: `http://192.168.1.100:5000`
4. **添加到主屏幕** (可选)
   - iOS: Safari → "添加到主屏幕"
   - Android: Chrome → "添加到主屏幕"

### 故障排除

#### 防火墙设置

**Windows:**
```powershell
netsh advfirewall firewall add rule name="Web Dashboard" dir=in action=allow protocol=TCP localport=5000
```

#### 修改端口

```bash
# 编辑 .env
WEB_PORT=8080

# 或临时修改
set WEB_PORT=8080
python web_dashboard.py
```

---

## 🔒 安全建议

### 1. 添加访问认证

编辑 `web_dashboard.py`:

```python
from flask import request, abort

API_TOKEN = "your-secret-token"

@app.before_request
def check_auth():
    token = request.headers.get('Authorization')
    if token != f'Bearer {API_TOKEN}':
        abort(401)
```

---

# 生产环境部署

## 🖥️ VPS部署

### 使用Gunicorn

```bash
# 安装Gunicorn
pip install gunicorn

# 启动
gunicorn -b 0.0.0.0:5000 -w 4 web_dashboard:app
```

### 使用Nginx反向代理

```nginx
server {
    listen 80;
    server_name proxy.yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 使用Systemd服务

创建 `/etc/systemd/system/proxy-dashboard.service`:

```ini
[Unit]
Description=Proxy Dashboard
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/project
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -b 0.0.0.0:5000 web_dashboard:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl enable proxy-dashboard
sudo systemctl start proxy-dashboard
```

---

## 🐳 Docker部署

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "web_dashboard.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  dashboard:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./proxies.db:/app/proxies.db
    environment:
      - WEB_PORT=5000
      - DATABASE_PATH=proxies.db
    restart: always
```

### 部署

```bash
docker-compose up -d
```

---

## 📊 部署方案对比

| 方案 | 成本 | 难度 | 速度 | 推荐度 |
|------|------|------|------|--------|
| **本地** | 免费 | ⭐ | 快 | ⭐⭐⭐ |
| **局域网** | 免费 | ⭐ | 快 | ⭐⭐⭐⭐ |

| **VPS** | $5/月 | ⭐⭐⭐ | 快 | ⭐⭐⭐⭐ |
| **Docker** | 免费 | ⭐⭐⭐ | 快 | ⭐⭐⭐⭐ |

---

## 🎯 推荐部署路线

### 阶段1: 本地测试
```bash
python web_dashboard.py
# http://localhost:5000
```

### 阶段2: 局域网使用
```bash
# 已配置完成，直接使用
# http://你的IP:5000
```

### 阶段3: 公网访问



**有VPS → Nginx + SSL**
```bash
# VPS部署 + Let's Encrypt
```

---

**部署完成！** 选择适合您的部署方式开始使用。
