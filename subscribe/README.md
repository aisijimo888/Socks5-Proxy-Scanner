# SOCKS5 代理订阅

本项目通过 GitHub Actions 自动扫描和验证 SOCKS5 代理，每 6 小时更新一次。

---

## 🚀 快速开始

### 主订阅链接（推荐）

```
https://raw.githubusercontent.com/你的用户名/Socks5-Proxy-Scanner/main/socks5.txt
```

直接复制链接使用即可！✨

---

## 📋 所有订阅链接

### SOCKS5 专用订阅

**标准版** - 所有有效代理（评分 >= 10）
```
https://raw.githubusercontent.com/你的用户名/仓库名/main/subscribe/socks5-all.txt
```

**高质量版** - 优质代理（评分 >= 70）⭐ 推荐
```
https://raw.githubusercontent.com/你的用户名/仓库名/main/subscribe/socks5-premium.txt
```

**快速版** - 快速响应（< 2s）
```
https://raw.githubusercontent.com/你的用户名/仓库名/main/subscribe/socks5-fast.txt
```

### 按国家分类

**美国代理**
```
https://raw.githubusercontent.com/你的用户名/仓库名/main/subscribe/by-country/socks5-US.txt
```

**日本代理**
```
https://raw.githubusercontent.com/你的用户名/仓库名/main/subscribe/by-country/socks5-JP.txt
```

**更多国家**: 查看 `subscribe/by-country/` 目录

### 传统格式订阅

- **Clash**: `https://raw.githubusercontent.com/用户名/仓库/main/subscribe/clash.yaml`
- **V2Ray**: `https://raw.githubusercontent.com/用户名/仓库/main/subscribe/v2ray.json`
- **纯文本**: `https://raw.githubusercontent.com/用户名/仓库/main/subscribe/proxies.txt`

---

## 🔄 更新频率

- **自动更新**: 每 6 小时运行一次
- **更新时间**: 00:00, 06:00, 12:00, 18:00 UTC

---

## ⚡ GitHub Pages 访问（可选，CDN 加速）

**启用方法**: Settings → Pages → Source 选择 `gh-pages` 分支

**主订阅**:
```
https://你的用户名.github.io/仓库名/subscribe/socks5-all.txt
```

**高质量版**:
```
https://你的用户名.github.io/仓库名/subscribe/socks5-premium.txt
```

**按国家**:
```
https://你的用户名.github.io/仓库名/subscribe/by-country/socks5-US.txt
```

---

## 💡 使用方法

### 命令行

```bash
# 下载标准订阅
curl https://raw.githubusercontent.com/用户名/仓库/main/socks5.txt

# 下载高质量版
curl https://raw.githubusercontent.com/用户名/仓库/main/subscribe/socks5-premium.txt

# 测试第一个代理
proxy=$(curl -s URL | grep -v '^#' | head -1)
curl --socks5 $proxy https://ipinfo.io
```

### 程序中使用

```python
import requests

# 获取代理列表
url = "https://raw.githubusercontent.com/用户名/仓库/main/subscribe/socks5-all.txt"
response = requests.get(url)
proxies = [line for line in response.text.split('\n') 
           if line and not line.startswith('#')]

print(f"获取到 {len(proxies)} 个代理")
```

---

## ⚠️ 使用说明

本项目收集的代理均来自公开源，仅供**学习研究**使用。

- ✅ 个人学习和研究
- ✅ 网络连接测试
- ❌ 请勿用于非法用途
- ❌ 请勿商业滥用

---

**注意**: 请将上述链接中的 `你的用户名` 和 `仓库名` 替换为实际值。
