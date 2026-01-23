# SOCKS5 Proxy Scanner

> A SOCKS5 proxy scanner and management tool. (中文项目 / Chinese Project)

高效的SOCKS5代理扫描与管理工具

---

## ⚠️ 免责声明 / Disclaimer

**中文:**

本项目仅供学习、研究和合法的网络测试使用。使用本工具时，请遵守当地法律法规及网络服务条款。开发者不对使用本工具造成的任何后果负责。

**English:**

This project is for educational, research, and legitimate network testing purposes only. Users must comply with local laws, regulations, and terms of service. The developer assumes no responsibility for any consequences resulting from the use of this tool.

---

## 🎯 适用场景 / Use Cases

**✅ 合法用途:**
- 📚 学习Python异步编程和网络编程
- 🔬 网络安全研究和测试
- 🛠️ 代理池管理和质量监控
- 🧪 网络连接测试和性能分析
- 📊 数据采集项目的代理管理

**❌ 禁止用途:**
- 非法访问受保护的网络资源
- 绕过地理限制或访问控制
- 侵犯他人隐私或进行恶意活动
- 任何违反法律法规的行为

**使用本工具即表示您同意仅将其用于合法目的。**

---

## ✨ 核心特性

### 基础功能
- 🚀 **简洁高效**: 代码结构清晰，易于维护
- 🔄 **模块化设计**: 分离代理源、验证器、导出器
- 📊 **智能评分**: 基于多维度的综合评分系统
- 🌐 **多源采集**: 支持25+个高质量代理源
- 📁 **多格式导出**: JSON、TXT、CSV格式
- ⚡ **并发控制**: 可配置的并发限制

### 🆕 增强功能

#### 1. 数据持久化 (SQLite)
- 📚 代理历史记录存储
- 📈 长期统计分析
- 🔄 自动清理过期数据
- ⚡ 高性能查询索引

#### 2. 增强评分系统 (100分制)
- **延迟评分** (30%) - 响应时间越快得分越高
- **稳定性评分** (20%) - 基于历史成功率
- **ISP类型** (15%) - 住宅IP优先
- **地理位置** (15%) - 目标国家加分
- **历史表现** (20%) - 长期可用性奖励

#### 3. 🛡️ 代理源健康监控 & 智能超时
- 🚀 **智能超时 (Smart Timeouts)**: 连接超时(5s) vs 传输超时(10s)，快速剔除死代理
- 实时检测源可用性
- 统计源质量(有效代理比例)
- 自动禁用失效源
- 生成源质量报告

#### 4. 📝 黑名单与订阅管理
- **自动黑名单**: 自动过滤掉长期失效的代理
- **黑名单导出**: 生成 `subscribe/blacklist.txt`
- **Telegram集成** (下文详述)
- 🤖 **Bot命令**
  - `/stats` - 查看代理池统计
  - `/best` - 获取最佳代理
  - `/sources` - 代理源状态
  - `/health` - 数据库健康检查
- 📡 **频道抓取**: 从Telegram频道自动抓取代理

#### 5. Web Dashboard
- 📊 实时统计卡片
- 📈 交互式图表 (Chart.js)
- 🔍 搜索和过滤
- 📋 代理列表表格
- 🌙 现代化深色主题
- 🔄 自动刷新 (30秒)

#### 6. 🔗 订阅链接系统（全新升级）⭐
- 📱 **多格式支持**
  - Clash YAML - 完整配置
  - V2Ray JSON - 标准格式
  - ShadowRocket - Base64编码
  - 通用 Base64 - 兼容多客户端
  - 纯文本 - 直接使用
- 🎯 **SOCKS5 专用订阅**（新增）
  - **标准版** (`socks5-all.txt`) - 所有有效代理
  - **高质量版** (`socks5-premium.txt`) - 评分 >= 70
  - **快速版** (`socks5-fast.txt`) - 响应 < 2s
- 🌍 **按国家分类订阅**（新增）
  - 自动生成美国、日本、德国等国家的专属订阅
  - 目录：`subscribe/by-country/socks5-*.txt`
- 🔄 **自动更新**: GitHub Actions 每6小时更新
- 🌐 **双重访问方式**: 
  - GitHub Raw URL（稳定）
  - GitHub Pages（CDN 加速）

#### 7. GitHub Actions自动化（性能优化）
- ⏰ 自动更新频率提升至每6小时 (00:00, 06:00, 12:00, 18:00 UTC)
- ⚡ 并发扫描提升至 150（性能提升50%）
- 📦 自动提交最新数据和订阅文件
- 📊 Actions Summary 显示详细统计
- 📧 成功/失败时Telegram通知
- 🚀 自动部署到 GitHub Pages（CDN 加速）

## 📦 安装依赖

### 基础依赖
```bash
pip install aiohttp aiohttp-socks python-dotenv
```

### 完整依赖 (包含所有增强功能)
```bash
pip install -r requirements.txt
```

**依赖说明:**
- `flask` + `flask-cors` - Web Dashboard
- `pyTelegramBotAPI` - Telegram Bot
- `telethon` - Telegram频道抓取
- `plotly` - 数据可视化

## 🚀 快速开始

### 1. 基础扫描 (传统模式)
```bash
python proxy_scanner_fixed.py
```

### 2. 增强扫描 (推荐)
```bash
# 基础增强扫描
python proxy_scanner_enhanced.py

# 启用所有功能
python proxy_scanner_enhanced.py --enable-enhanced --check-sources

# 自定义参数
python proxy_scanner_enhanced.py \
  --timeout 15 \
  --max-concurrency 100 \
  --db-path my_proxies.db \
  --cleanup-days 60
```

### 3. 启动Web Dashboard
```bash
python web_dashboard.py
```
然后访问: 
- **本地**: http://localhost:5000
- **局域网**: http://你的IP地址:5000 (同WiFi下的手机/平板可访问)
- **公网**: 参见 [部署指南](docs/DEPLOYMENT_GUIDE.md#cloudflare公网部署)

### 4. 启动Telegram Bot
```bash
# 首先配置.env文件
cp .env.example .env
# 编辑.env填入TELEGRAM_BOT_TOKEN

python telegram_bot.py
```


### 5. 使用订阅链接 ⭐（推荐）

**主订阅链接**（根目录，最简单）:
```
https://raw.githubusercontent.com/你的用户名/仓库名/main/socks5.txt
```

**SOCKS5 专用订阅**:
```
# 标准版 - 所有有效代理（评分 >= 10）
https://raw.githubusercontent.com/你的用户名/仓库名/main/subscribe/socks5-all.txt

# 高质量版 - 优质代理（评分 >= 70）⭐ 推荐
https://raw.githubusercontent.com/你的用户名/仓库名/main/subscribe/socks5-premium.txt

# 快速版 - 快速响应（< 2s）
https://raw.githubusercontent.com/你的用户名/仓库名/main/subscribe/socks5-fast.txt
```

**按国家分类**:
```
# 美国代理
https://raw.githubusercontent.com/你的用户名/仓库名/main/subscribe/by-country/socks5-US.txt

# 日本代理
https://raw.githubusercontent.com/你的用户名/仓库名/main/subscribe/by-country/socks5-JP.txt
```

**传统格式订阅**:
```
# Clash 订阅
https://raw.githubusercontent.com/你的用户名/仓库名/main/subscribe/clash.yaml

# V2Ray 订阅
https://raw.githubusercontent.com/你的用户名/仓库名/main/subscribe/v2ray.json
```

**使用方法**:
```bash
# 下载代理列表
curl https://raw.githubusercontent.com/你的用户名/仓库名/main/socks5.txt

# 测试第一个代理
proxy=$(curl -s URL | grep -v '^#' | head -1)
curl --socks5 $proxy https://ipinfo.io
```

**可选：GitHub Pages 访问（CDN 加速）**

推送后启用 Pages (Settings → Pages → gh-pages 分支)：
```
# 标准版（CDN 加速）
https://你的用户名.github.io/仓库名/subscribe/socks5-all.txt

# 高质量版（CDN 加速）
https://你的用户名.github.io/仓库名/subscribe/socks5-premium.txt
```

### 6. 生成订阅文件
```bash
# 从数据库生成所有格式的订阅文件
python subscription_generator.py

# 生成的文件保存在 subscribe/ 目录:
# SOCKS5 专用:
# - socks5-all.txt (标准版)
# - socks5-premium.txt (高质量版)
# - socks5-fast.txt (快速版)
# - by-country/socks5-*.txt (按国家分类)
#
# 传统格式:
# - clash.yaml (Clash)
# - v2ray.json (V2Ray)
# - shadowrocket.txt (ShadowRocket)
# - base64.txt (通用Base64)
# - proxies.txt (纯文本)
```

## 📱 客户端配置指南

### Clash
1. 复制 Clash 订阅链接
2. 打开 Clash 客户端
3. 配置 → 添加 →  <订阅 URL>
4. 更新订阅

### V2RayN/V2RayNG
1. 复制 V2Ray 订阅链接
2. 打开 V2RayN/V2RayNG
3. 订阅 → 订阅设置 → 添加
4. 输入订阅 URL
5. 更新订阅

### ShadowRocket (iOS)
1. 复制 ShadowRocket 订阅链接
2. 打开 ShadowRocket
3. 右上角 + → Subscribe
4. 粘贴 URL
5. 完成

## 📚 文档

**核心文档:**
- [配置指南](docs/CONFIGURATION_GUIDE.md) - 超时、黑名单、国家白名单配置
- [部署指南](docs/DEPLOYMENT_GUIDE.md) - Web Dashboard、局域网、Cloudflare部署
- [高级用法](docs/ADVANCED_USAGE.md) - 数据库查询、性能优化、API集成
- [项目结构](docs/PROJECT_STRUCTURE.md) - 文件说明、开发指南

**优化文档:**（新增）
- [优化总结](OPTIMIZATION_SUMMARY.md) - 所有优化改进的完整记录
- [项目审计](PROJECT_AUDIT.md) - 文件输出流程和问题修复
- [订阅说明](subscribe/README.md) - GitHub Pages 订阅链接使用指南

---

## 🔧 配置说明

### 环境变量配置 (.env)

复制示例文件并编辑:
```bash
cp .env.example .env
```

**重要配置项:**
```env
# Telegram Bot Token (从 @BotFather 获取)
TELEGRAM_BOT_TOKEN=your_token_here

# Web Dashboard端口
WEB_PORT=5000

# 数据库路径
DATABASE_PATH=proxies.db

# 功能开关
ENABLE_TELEGRAM=True
ENABLE_WEB=True
```

### 代理源配置 (config.py)

项目已内置25+个高质量代理源，包括:
- GitHub自动更新源 (15个)
- 专业API服务 (4个)
- 社区维护源 (6个)

可以编辑 `config.py` 添加自定义源。

## 📊 命令行参数

### proxy_scanner_enhanced.py
```bash
--timeout <秒>              # 超时时间 (默认10)
--max-concurrency <数量>    # 最大并发 (默认50)
--output <文件>              # 输出文件 (默认proxies.json)
--db-path <路径>             # 数据库路径 (默认proxies.db)
--cleanup-days <天数>        # 清理天数 (默认30)
--enable-enhanced           # 启用增强验证 (DNS泄露、带宽测试)
--check-sources            # 检查代理源健康状况
--log-level <级别>          # 日志级别 (DEBUG/INFO/WARNING/ERROR)
```

## 📁 输出文件

扫描完成后会生成:

1. **proxies.json** - 详细信息 (JSON格式)
2. **proxies.txt** - 纯代理列表 (`ip:port`)
3. **proxies.csv** - 详细信息表格
4. **best_proxies.txt** - 最佳代理列表 (基于综合评分)
5. **blacklist.txt** - 代理黑名单
6. **proxies.db** - SQLite数据库 (历史记录)

## 🏗️ 架构设计

```
proxy_scanner_enhanced.py      # 增强主程序
├── config.py                  # 基础配置
├── config_manager.py          # 环境变量管理
├── proxy_sources_fixed.py     # 代理源管理器
├── validators.py              # 标准验证器
├── enhanced_validator.py      # 增强验证器
├── proxy_database.py          # 数据库管理
├── source_health_checker.py   # 源健康检查
├── exporters.py               # 结果导出器
├── telegram_bot.py            # Telegram Bot
├── telegram_scraper.py        # Telegram抓取器
└── web_dashboard.py           # Web Dashboard

templates/                     # Web模板
└── index.html

static/                        # 静态资源
├── css/dashboard.css
└── js/dashboard.js
```

## 📈 Web Dashboard功能

### 主要模块
1. **统计卡片** - 实时显示总代理数、活跃数、成功率
2. **国家分布图** - 饼图展示代理地理分布
3. **代理源状态** - 柱状图显示各源贡献
4. **代理列表** - 可搜索、排序、过滤的表格
5. **代理详情** - 点击查看单个代理完整信息

### API端点
**基础端点**
- `GET /api/stats` - 获取统计数据
- `GET /api/proxies` - 获取代理列表
- `GET /api/proxy/<address>` - 获取单个代理详情
- `GET /api/sources` - 获取代理源状态
- `GET /api/export?format=json|txt|csv` - 导出代理
- `POST /api/cleanup` - 触发数据库清理

**订阅端点** 🆕
- `GET /api/subscribe/clash` - Clash YAML 订阅
- `GET /api/subscribe/v2ray` - V2Ray JSON 订阅
- `GET /api/subscribe/base64` - Base64 编码订阅
- `GET /api/subscribe/shadowrocket` - ShadowRocket 订阅
- `GET /api/subscribe/plain` - 纯文本代理列表


## 🤖 Telegram使用指南

### 创建Bot
1. 在Telegram中找到 @BotFather
2. 发送 `/newbot` 创建机器人
3. 获取Bot Token并配置到`.env`

### Bot命令
- `/start` - 查看帮助
- `/stats` - 代理池统计
- `/best` - 最佳代理列表
- `/sources` - 代理源状态
- `/health` - 数据库健康检查
- 直接发送 `ip:port` - 查询代理信息

### 频道抓取 (高级)
需要安装 `telethon` 并配置API ID/Hash:
```python
from telegram_scraper import TelegramScraper
scraper = TelegramScraper(api_id, api_hash, phone)
await scraper.start()
proxies = await scraper.scrape_channel('@socks5list')
```

## ⚙️ GitHub Actions设置

### 1. 配置Secrets
在GitHub仓库设置中添加:
- `TELEGRAM_BOT_TOKEN` (可选)
- `TELEGRAM_CHAT_ID` (可选)

### 2. 启用工作流
推送代码后，工作流会:
- 每小时自动运行
- 扫描并更新代理池
- 提交最新数据到仓库
- 失败时发送Telegram通知

### 3. 手动触发
在GitHub Actions页面点击 "Run workflow"

## 🔍 高级功能

### 数据库查询示例
```python
from proxy_database import ProxyDatabase

db = ProxyDatabase()

# 获取最佳代理
best = db.get_best_proxies(limit=10, min_success_rate=0.8)

# 获取代理统计
stats = db.get_proxy_stats('1.2.3.4:1080')

# 获取源健康状况
sources = db.get_source_health()

# 清理旧数据
db.cleanup_old_records(days=30)
```

### 源健康检查
```python
from source_health_checker import SourceHealthChecker

checker = SourceHealthChecker()
results = await checker.check_all_sources(sources)
report = checker.generate_report(results)
print(report)
```

## 🎯 SOCKS5源推荐

### GitHub源 (自动更新, 推荐)
- TheSpeedX/SOCKS-List ⭐⭐⭐⭐⭐
- monosans/proxy-list ⭐⭐⭐⭐⭐
- hookzof/socks5_list ⭐⭐⭐⭐
- mmpx12/proxy-list ⭐⭐⭐⭐
- roosterkid/openproxylist ⭐⭐⭐

### API源 (高质量)
- ProxyScrape API
- GeoNode API
- ProxyList+ API

### Telegram频道
- @socks5list
- @proxy_mtm
- @free_proxy_vpn

## 🛠️ 故障排除

### 常见问题

**Q: Web Dashboard无法访问**
```bash
# 检查端口是否被占用
netstat -ano | findstr :5000

# 修改端口
set WEB_PORT=8080
python web_dashboard.py
```

**Q: Telegram Bot不响应**
```bash
# 验证Token
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe

# 检查日志
python telegram_bot.py
```

**Q: 数据库错误**
```bash
# 删除并重新初始化
rm proxies.db
python proxy_scanner_enhanced.py
```

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request!

---

**项目亮点:**
- ✅ 25+ 高质量代理源
- ✅ SQLite持久化存储
- ✅ 多维度智能评分（100分制）
- ✅ Web可视化监控
- ✅ Telegram Bot集成
- ✅ 🆕 多层级 SOCKS5 订阅系统（标准/高质量/快速）
- ✅ 🆕 按国家分类订阅
- ✅ 🆕 GitHub Pages 自动部署（CDN 加速）
- ✅ 🆕 性能优化（6h更新频率 + 150并发）
- ✅ 🆕 时区准确处理（UTC存储 + 北京时间显示）
- ✅ GitHub Actions全自动化 + 统计输出
- ✅ 模块化架构设计


**⭐ 如果觉得有用，请给个Star!**