# 项目文件结构说明

## 📁 当前项目结构

```
d:/VPN/jiakuan/
├── 🎯 主程序
│   └── proxy_scanner_enhanced.py       # 主扫描器入口
│
├── 🔧 核心模块
│   ├── config.py                       # 基础配置
│   ├── config_manager.py               # 环境变量管理
│   ├── proxy_sources_fixed.py          # 代理源管理
│   ├── validators.py                   # 标准验证器
│   ├── exporters.py                    # 结果导出
│   ├── proxy_database.py               # 数据库管理(含黑名单)
│   ├── enhanced_validator.py           # 增强验证器
│   └── source_health_checker.py        # 源健康检查
│
├── 🤖 集成功能
│   ├── telegram_bot.py                 # Telegram Bot
│   ├── telegram_scraper.py             # Telegram抓取
│   └── web_dashboard.py                # Web Dashboard
│
├── 🛠️ 工具和演示
│   └── demo.py                         # 功能演示
│
├── 🌐 Web前端
│   ├── templates/
│   │   └── index.html                  # Dashboard HTML
│   └── static/
│       ├── css/dashboard.css           # 样式
│       └── js/dashboard.js             # 前端逻辑
│
├── ⚙️ 自动化
│   └── .github/workflows/
│       └── auto-update-proxies.yml     # GitHub Actions
│
├── 📝 配置文件
│   ├── .env.example                    # 环境变量模板
│   └── requirements.txt                # 依赖列表
│
├── 📚 文档
│   ├── README.md                       # 主文档
│   ├── ADVANCED_USAGE.md               # 高级用法
│   ├── TIMEOUT_CONFIG_GUIDE.md         # 超时配置
│   └── BLACKLIST_OPTIMIZATION.md       # 黑名单优化
│
├── 📊 数据文件 (运行时生成)
│   ├── proxies.db                      # SQLite数据库 ⭐
│   ├── demo.db                         # 演示数据库 (可删除)
│   ├── proxies.json/txt/csv            # 导出结果
│   ├── best_proxies.txt                # 最佳代理
│   └── scanner.log                     # 运行日志
│
└── 📦 资源文件
    ├── GeoLite2-ASN.mmdb               # GeoIP数据库
    └── Industrial_Socks5.txt           # 自定义代理列表
```

## 🗂️ 文件分类

### 核心文件 (必须保留)
- **主程序**: `proxy_scanner_enhanced.py`
- **核心模块**: 8个 (config, validators, database等)
- **配置**: `.env.example`, `requirements.txt`
- **文档**: 4个MD文件

### 功能模块 (按需使用)
- **Telegram**: `telegram_bot.py`, `telegram_scraper.py`
- **Web**: `web_dashboard.py`, `templates/`, `static/`
- **工具**: `demo.py`

### 临时/可删除文件
- ❌ `demo.db` - 演示数据库
- ❌ `proxy_history.json` - 未使用
- ⚠️ `proxies.json/txt/csv` - 示例数据(首次运行后可删除)

## 🎯 文件用途速查

| 文件 | 用途 | 是否必需 |
|------|------|---------|
| `proxy_scanner_enhanced.py` | 主扫描器 | ✅ 必需 |
| `proxy_database.py` | 数据持久化+黑名单 | ✅ 必需 |
| `enhanced_validator.py` | 增强验证+评分 | ✅ 必需 |
| `web_dashboard.py` | Web界面 | ⚠️ 可选 |
| `telegram_bot.py` | Telegram Bot | ⚠️ 可选 |
| `demo.py` | 功能演示 | ⚠️ 开发用 |
| `GeoLite2-ASN.mmdb` | IP地理信息 | ⚠️ 增强功能需要 |

## 📋 清理建议

### 选项1: 最小化清理 (推荐)
```bash
# 只删除明确无用的文件
rm demo.db
rm proxy_history.json
```

### 选项2: 完整清理
```bash
# 删除所有临时和示例数据
rm demo.db
rm proxy_history.json
rm proxies.json proxies.txt proxies.csv
rm scanner.log
```

### 选项3: 重置项目
```bash
# 删除所有运行时生成的数据(慎用)
rm *.db
rm *.json
rm *.txt
rm *.csv
rm *.log
```

## 🚀 推荐的.gitignore

如果要提交到Git，建议忽略:

```gitignore
# 数据库
*.db

# 日志
*.log

# 代理数据
proxies.json
proxies.txt
proxies.csv
best_proxies.txt

# 环境变量
.env

# Python缓存
__pycache__/
*.pyc
*.pyo

# IDE
.vscode/
.idea/

# 临时文件
*.tmp
*.bak
```

## 📊 项目统计

- **总文件**: ~30个
- **Python代码**: 13个
- **文档**: 4个
- **配置**: 2个
- **Web资源**: 3个 (HTML/CSS/JS)
- **自动化**: 1个 (GitHub Actions)

## 💡 维护建议

1. **定期清理**
   ```bash
   # 每月清理旧数据
   python -c "from proxy_database import *; ProxyDatabase().cleanup_old_records(30)"
   ```

2. **版本控制**
   - 提交代码文件
   - 忽略数据文件
   - 忽略日志和缓存

3. **备份重要数据**
   ```bash
   # 备份数据库
   cp proxies.db backup/proxies_$(date +%Y%m%d).db
   ```

## 🎯 快速参考

**日常使用需要的文件:**
- `proxy_scanner_enhanced.py` + 核心模块 + `proxies.db`

**可选功能需要的文件:**
- Telegram: `telegram_bot.py`, `telegram_scraper.py`
- Web: `web_dashboard.py`, `templates/`, `static/`

**开发/测试需要的文件:**
- `demo.py` - 功能演示

---

**总结**: 项目文件已经很精简，只需删除 `demo.db` 和 `proxy_history.json` 即可。
