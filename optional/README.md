# Optional Features

此目录包含可选功能模块，用于 Docker/VPS 本地部署场景。

## 📁 目录结构

```
optional/
├── web/                    # Web 面板（本地部署）
│   ├── web_dashboard.py   # Flask 主程序
│   ├── proxy_api.py       # RESTful API
│   ├── templates/         # HTML 模板
│   └── static/            # 静态资源（CSS/JS）
│
├── telegram/              # Telegram Bot
│   └── telegram_bot.py    # Bot 主程序
│
└── subscription/          # 订阅生成器
    ├── subscription_generator.py
    └── proxy_client.py
```

---

## 🚀 使用方式

### Web 面板（Docker/VPS）

**启动 Web Dashboard：**
```bash
cd optional/web
python web_dashboard.py
```

访问：`http://localhost:5000`

**启动 API 服务器：**
```bash
cd optional/web
python proxy_api.py
```

API 端点：
- `GET /api/stats` - 统计信息
- `GET /api/proxies` - 代理列表
- `GET /api/proxy/<address>` - 单个代理详情
- `GET /api/sources` - 代理源状态

---

### Telegram Bot

**配置：**
```bash
# 编辑 .env
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id
```

**启动：**
```bash
cd optional/telegram
python telegram_bot.py
```

**Bot 命令：**
- `/start` - 查看帮助
- `/stats` - 代理池统计
- `/best` - 最佳代理列表
- `/sources` - 代理源状态
- `/health` - 数据库健康检查

---

### 订阅生成器

**生成订阅文件：**
```bash
cd optional/subscription
python subscription_generator.py
```

生成的文件保存在 `subscribe/` 目录：
- `socks5-all.txt` - 全部代理
- `socks5-premium.txt` - 高质量代理
- `socks5-fast.txt` - 快速代理
- `by-country/socks5-*.txt` - 按国家分类

---

## 📦 依赖

这些功能需要额外的依赖：

```bash
pip install flask flask-cors pyTelegramBotAPI
```

---

## ⚠️ 注意事项

1. **GitHub Actions 不需要这些文件**
   - Actions 自动运行核心扫描器
   - Cloudflare Pages 提供前端和 API

2. **仅用于本地/VPS 部署**
   - Web Dashboard 需要持续运行的服务器
   - Telegram Bot 需要长连接

3. **端口配置**
   - Web Dashboard: 默认 5000（可通过 `WEB_PORT` 环境变量修改）
   - API Server: 默认 5000

---

## 🐳 Docker 部署（待实现）

```dockerfile
# 示例 Dockerfile
FROM python:3.8-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "optional/web/web_dashboard.py"]
```

---

**这些功能是可选的，不影响 GitHub Actions + Cloudflare Pages 的核心部署。**
