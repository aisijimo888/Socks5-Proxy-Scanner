# Telegram 频道代理源集成指南

## 🎯 概述

项目已支持从 Telegram 频道抓取 SOCKS5 代理！有两种使用方式：

---

## 📱 方式一：简化版（推荐新手）

**无需 Telegram API**，直接从公开频道抓取

### 使用方法

```python
from telegram_scraper import SimpleTelegramScraper
import asyncio

async def scrape_telegram_channels():
    scraper = SimpleTelegramScraper()
    
    # 推荐的 SOCKS5 频道
    channels = [
        'socks5list',
        'proxy_mtm',
        'free_proxy_vpn',
        'proxies_list',
        'socks5_channel'
    ]
    
    all_proxies = set()
    for channel in channels:
        proxies = await scraper.scrape_channel_messages(channel)
        all_proxies.update(proxies)
        print(f"从 @{channel} 获取到 {len(proxies)} 个代理")
    
    print(f"\n总计: {len(all_proxies)} 个代理")
    return all_proxies

# 运行
asyncio.run(scrape_telegram_channels())
```

**优点：**
- ✅ 无需 API 认证
- ✅ 简单快速
- ✅ 适合自动化

**缺点：**
- ⚠️ 只能抓取公开频道
- ⚠️ 抓取数量有限（Web 预览限制）

---

## 🔑 方式二：完整版（推荐高级用户）

**需要 Telegram API**，功能强大

### 1. 获取 Telegram API 凭据

**步骤：**
1. 访问 https://my.telegram.org/apps
2. 登录你的 Telegram 账号
3. 创建应用，获取：
   - `API ID` (数字)
   - `API Hash` (字符串)

### 2. 配置环境变量

创建 `.env` 文件：
```env
# Telegram API 配置
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_PHONE=+86XXXXXXXXXXX  # 你的手机号
```

### 3. 安装依赖

```bash
pip install telethon
```

### 4. 使用完整抓取器

```python
from telegram_scraper import TelegramScraper
import asyncio

async def scrape_with_api():
    scraper = TelegramScraper(
        api_id=12345678,  # 你的 API ID
        api_hash='your_api_hash',
        phone='+86XXXXXXXXXXX'
    )
    
    # 启动（首次需要验证码）
    await scraper.start()
    
    # 推荐频道
    channels = [
        '@socks5list',
        '@proxy_mtm',
        '@free_proxy_vpn',
        '@proxies_list',
        '@socks5_channel',
        '@ProxyMTProto',
        '@V2List',
        '@free_v2ray',
    ]
    
    # 抓取所有频道（每个频道最近 100 条消息）
    proxies = await scraper.scrape_multiple_channels(channels, limit=100)
    
    print(f"总计抓取: {len(proxies)} 个代理")
    
    # 保存到文件
    with open('telegram_proxies.txt', 'w') as f:
        for proxy in proxies:
            f.write(f"{proxy}\n")
    
    await scraper.close()

# 运行
asyncio.run(scrape_with_api())
```

**优点：**
- ✅ 可以抓取更多频道
- ✅ 无抓取数量限制
- ✅ 可以实时监听新消息
- ✅ 更稳定可靠

---

## 🔄 集成到自动化工作流

### GitHub Actions 集成（本地运行需要）

由于 GitHub Actions 无法交互式验证 Telegram，建议：

**方式1：本地定期运行**
```bash
# 每天本地运行一次
python telegram_scraper_runner.py
git add telegram_proxies.txt
git push
```

**方式2：使用简化版集成（推荐）**

创建 `telegram_proxy_sources.py`:
```python
"""从 Telegram 频道抓取代理并添加到主扫描器"""
import asyncio
from telegram_scraper import SimpleTelegramScraper

async def get_telegram_proxies():
    """获取 Telegram 代理源"""
    scraper = SimpleTelegramScraper()
    
    channels = [
        'socks5list',
        'proxy_mtm',
        'free_proxy_vpn',
    ]
    
    all_proxies = set()
    for channel in channels:
        try:
            proxies = await scraper.scrape_channel_messages(channel)
            all_proxies.update(proxies)
        except Exception as e:
            print(f"抓取 @{channel} 失败: {e}")
    
    return list(all_proxies)

if __name__ == '__main__':
    proxies = asyncio.run(get_telegram_proxies())
    print(f"从 Telegram 频道获取到 {len(proxies)} 个代理")
    
    # 保存到文件
    with open('telegram_socks5.txt', 'w') as f:
        for proxy in proxies:
            f.write(f"{proxy}\n")
```

---

## 📋 推荐的 SOCKS5 Telegram 频道

### 🌟 高质量频道
- [@socks5list](https://t.me/socks5list) - 专注 SOCKS5
- [@proxy_mtm](https://t.me/proxy_mtm) - MTProto 代理
- [@free_proxy_vpn](https://t.me/free_proxy_vpn) - 免费代理

### 📊 大型频道
- [@proxies_list](https://t.me/proxies_list) - 各类代理
- [@V2List](https://t.me/V2List) - V2Ray 订阅
- [@ProxyMTProto](https://t.me/ProxyMTProto) - MTProto

### 🔸 其他频道
- [@socks5_channel](https://t.me/socks5_channel)
- [@free_v2ray](https://t.me/free_v2ray)
- [@vpnpool_proxypool](https://t.me/vpnpool_proxypool)

---

## 🚀 快速开始

### 最简单的方式（5分钟）

```bash
# 1. 运行简化版抓取器
python -c "
from telegram_scraper import SimpleTelegramScraper
import asyncio

async def main():
    scraper = SimpleTelegramScraper()
    proxies = await scraper.scrape_channel_messages('socks5list')
    with open('tg_proxies.txt', 'w') as f:
        for p in proxies:
            f.write(f'{p}\n')
    print(f'获取到 {len(proxies)} 个代理')

asyncio.run(main())
"

# 2. 查看结果
cat tg_proxies.txt
```

---

## ⚠️ 注意事项

1. **速率限制**
   - Telegram 有 API 调用限制
   - 建议每小时抓取一次即可

2. **代理质量**
   - TG 频道的代理质量参差不齐
   - 建议配合验证器使用
   - 失效率可能较高

3. **隐私安全**
   - 不要泄露 API ID 和 Hash
   - 不要将 session 文件提交到 Git

4. **频道失效**
   - 部分频道可能被封禁或删除
   - 定期更新频道列表

---

## 💡 推荐使用方案

**对于个人使用：**
1. ✅ 使用简化版 `SimpleTelegramScraper`
2. ✅ 每天运行一次
3. ✅ 结合 GitHub 源使用

**对于生产环境：**
1. ✅ 使用完整版 `TelegramScraper` 
2. ✅ 实时监听频道新消息
3. ✅ 自动验证并更新

---

## 🔧 故障排除

**Q: 抓取到 0 个代理？**
- 检查频道是否存在
- 检查网络连接
- 尝试访问 https://t.me/频道名 确认

**Q: 需要验证码？**
- 首次使用完整版需要输入验证码
- 之后会保存 session，无需重复验证

**Q: API 错误？**
- 确认 API ID 和 Hash 正确
- 确认手机号格式正确（+86开头）

---

**总结：Telegram 频道是很好的代理源补充，配合 GitHub 源使用效果最佳！** 🎉
