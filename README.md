# SOCKS5 Proxy Scanner

> 高效的 SOCKS5 代理扫描与管理工具 | Efficient SOCKS5 proxy scanning and management tool

[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Automated-brightgreen)](https://github.com/features/actions)
[![Cloudflare Pages](https://img.shields.io/badge/Cloudflare-Pages-orange)](https://pages.cloudflare.com/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)

---

## ⚠️ 免责声明 / Disclaimer

**中文:**

本项目仅供学习、研究和合法的网络测试使用。使用本工具时，请遵守当地法律法规及网络服务条款。开发者不对使用本工具造成的任何后果负责。

**English:**

This project is for educational, research, and legitimate network testing purposes only. Users must comply with local laws, regulations, and terms of service. The developer assumes no responsibility for any consequences resulting from the use of this tool.

---

## ✨ 核心特性

### 自动化部署
- ☁️ **Cloudflare Pages** - 无服务器前端，全球CDN加速
- 📦 **Cloudflare KV** - 全球分布式代理数据存储
- 🔄 **GitHub Actions** - 每6小时自动扫描更新
- 📊 **可视化面板** - 实时监控代理池状态

### 代理管理
- 🔍 **自动扫描** - 25+ 高质量代理源
- ✅ **增强验证** - 连接测试 + DNS泄漏检测
- 📊 **智能评分** - 多维度综合评分系统
- 🚫 **黑名单系统** - 自动过滤失败代理
- 📡 **Telegram集成** - 支持从频道抓取代理

### API 接口
- `GET /api/proxies` - 获取所有代理列表
- `GET /api/random` - 获取随机代理

---

## 🚀 快速开始

### 部署方式 1: GitHub Actions + Cloudflare Pages（推荐）

**优势：**
- ✅ 零维护成本
- ✅ 全球 CDN 加速
- ✅ 自动化更新
- ✅ 无需服务器

**部署步骤：**

1. **Fork 本仓库**

2. **配置 GitHub Secrets**

进入仓库 `Settings` → `Secrets and variables` → `Actions`，添加：

| Secret 名称 | 说明 |
|------------|------|
| `CLOUDFLARE_API_TOKEN` | Cloudflare API Token |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare 账户 ID |
| `KV_NAMESPACE_ID` | KV Namespace ID |

详细配置见：[Cloudflare KV 配置指南](.github/CLOUDFLARE_KV_SETUP.md)

3. **部署 Cloudflare Pages**

- 登录 Cloudflare → **Workers & Pages**
- 创建新项目，连接 GitHub 仓库
- 构建目录：`public`
- 绑定 KV Namespace（变量名：`PROXY_POOL`）

4. **启动自动化**

GitHub Actions 会每 6 小时自动运行，或手动触发

---

### 部署方式 2: 本地运行

**克隆仓库：**
```bash
git clone https://github.com/noxenys/Socks5-Proxy-Scanner.git
cd Socks5-Proxy-Scanner
```

**安装依赖：**
```bash
pip install -r requirements.txt
```

**配置环境变量：**
```bash
cp .env.example .env
# 编辑 .env 文件
```

**运行扫描器：**
```bash
python proxy_scanner_enhanced.py --max-concurrency 150
```

---

## 📁 项目结构

```
Socks5-Proxy-Scanner/
├── proxy_scanner_enhanced.py    # 主扫描器
├── proxy_database.py            # 数据库管理
├── enhanced_validator.py         # 代理验证
├── ip_reputation.py             # IP声誉检查
├── telegram_scraper.py          # Telegram抓取
│
├── public/                      # Cloudflare Pages前端
│   └── index.html              # 可视化面板
│
├── functions/                   # Serverless API
│   └── api/
│       ├── proxies.js          # 代理列表
│       └── random.js           # 随机代理
│
├── .github/
│   ├── workflows/
│   │   ├── auto-update-proxies.yml   # GitHub订阅
│   │   └── proxy_cron.yml            # Cloudflare同步
│   └── CLOUDFLARE_KV_SETUP.md        # KV配置指南
│
└── subscribe/                   # 订阅文件
    ├── socks5-all.txt          # 全部代理
    ├── socks5-premium.txt      # 高质量代理
    └── by-country/             # 按国家分类
```

---

## 📊 命令行参数

```bash
python proxy_scanner_enhanced.py \
  --timeout 10 \
  --max-concurrency 150 \
  --enable-enhanced \
  --check-sources
```

**参数说明：**
- `--timeout` - 超时时间（秒）
- `--max-concurrency` - 最大并发数
- `--enable-enhanced` - 启用增强验证
- `--check-sources` - 检查代理源健康

---

## 🔗 订阅链接

### SOCKS5 专用订阅

```
# 全部有效代理
https://raw.githubusercontent.com/noxenys/Socks5-Proxy-Scanner/main/subscribe/socks5-all.txt

# 高质量代理（评分≥70）⭐ 推荐
https://raw.githubusercontent.com/noxenys/Socks5-Proxy-Scanner/main/subscribe/socks5-premium.txt

# 快速代理（延迟<2s）
https://raw.githubusercontent.com/noxenys/Socks5-Proxy-Scanner/main/subscribe/socks5-fast.txt
```

### 按国家分类

```
# 美国代理
https://raw.githubusercontent.com/noxenys/Socks5-Proxy-Scanner/main/subscribe/by-country/socks5-US.txt

# 日本代理
https://raw.githubusercontent.com/noxenys/Socks5-Proxy-Scanner/main/subscribe/by-country/socks5-JP.txt
```

详见：[subscribe/README.md](subscribe/README.md)

---

## 🔧 环境变量

复制 `.env.example` 并编辑：

```env
# 数据库路径
DATABASE_PATH=proxies.db

# 扫描配置
SCAN_TIMEOUT=10
MAX_CONCURRENCY=150

# Cloudflare（仅 GitHub Actions）
CLOUDFLARE_API_TOKEN=your_token
CLOUDFLARE_ACCOUNT_ID=your_account_id
KV_NAMESPACE_ID=your_namespace_id
```

---

## 📈 数据流程

```
GitHub Actions（每6小时）
  ↓
运行扫描器 → 验证代理 → 生成 proxies.json
  ↓
上传到 Cloudflare KV（key: current_proxies）
  ↓
Cloudflare Pages Functions 读取KV
  ↓
前端页面通过 API 展示数据
```

---

## 🎯 代理源

项目内置 25+ 个高质量代理源，包括：

- GitHub 自动更新源（15个）
- 专业 API 服务（4个）
- 社区维护源（6个）

---

## 🛠️ 故障排查

**GitHub Actions 失败：**
- 检查 Secrets 配置是否正确
- 查看 Actions 日志详细错误

**Cloudflare Pages 无数据：**
- 检查 KV 绑定（变量名必须是 `PROXY_POOL`）
- 验证 KV 中是否有 `current_proxies` 键

**代理扫描慢：**
- 调整 `--max-concurrency` 参数
- 检查网络连接

---

## 📝 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**⭐ 如果觉得有用，请给个 Star！**