# 代理API使用指南

## 🚀 快速开始

### 1. 启动API服务器

```bash
# Windows
start_api.bat

# 或直接运行
python proxy_api.py
```

服务器将在 `http://localhost:8080` 启动

### 2. 在其他项目中使用

#### Python项目

```python
from proxy_client import ProxyClient

# 初始化客户端
client = ProxyClient('http://localhost:8080')

# 获取随机代理
proxy = client.get_random()
print(proxy)  # socks5://1.2.3.4:1080

# 在requests中使用
import requests
proxies = client.as_requests_proxies()
response = requests.get('http://httpbin.org/ip', proxies=proxies)
```

#### JavaScript/Node.js项目

```javascript
// 获取随机代理
const response = await fetch('http://localhost:8080/api/proxy/random');
const data = await response.json();
console.log(data.format);  // socks5://1.2.3.4:1080

// 使用代理
const axios = require('axios');
const proxy = data.format.replace('socks5://', '').split(':');
const agent = new HttpsProxyAgent({
    host: proxy[0],
    port: proxy[1]
});
```

#### cURL / 命令行

```bash
# 获取随机代理
curl http://localhost:8080/api/proxy/random

# 获取最佳代理列表
curl http://localhost:8080/api/proxy/best?limit=5

# 美国代理
curl http://localhost:8080/api/proxy/best?country=US

# 导出为文本
curl http://localhost:8080/api/export/txt > proxies.txt
```

---

## 📚 API端点

### GET /api/proxy/random
获取随机代理

**参数:**
- `country` (可选): 国家代码 (如 US, JP)
- `min_score` (可选): 最低评分 (0-100)

**返回:**
```json
{
    "address": "1.2.3.4:1080",
    "country": "United States",
    "country_code": "US",
    "score": 85.5,
    "success_rate": 0.95,
    "response_time": 1.23,
    "format": "socks5://1.2.3.4:1080"
}
```

### GET /api/proxy/best
获取最佳代理列表

**参数:**
- `limit` (可选): 返回数量 (默认10, 最大100)
- `country` (可选): 国家代码
- `min_score` (可选): 最低评分
- `format` (可选): simple | detailed

**返回:**
```json
{
    "count": 10,
    "proxies": ["1.2.3.4:1080", "5.6.7.8:1080", ...]
}
```

### GET /api/proxy/country/{code}
获取指定国家的代理

**示例:**
```bash
GET /api/proxy/country/US?limit=5
```

### GET /api/stats
获取代理池统计

### GET /api/export/{format}
导出代理列表

**格式:** txt | json | csv

---

## 💻 完整使用示例

### 示例1: 爬虫项目

```python
# spider.py
from proxy_client import ProxyClient
import requests

client = ProxyClient()

def crawl(url):
    """使用代理爬取"""
    for attempt in range(3):
        try:
            # 获取代理
            proxy = client.get_random(country='US')
            
            # 发送请求
            response = requests.get(
                url,
                proxies={'http': proxy, 'https': proxy},
                timeout=10
            )
            
            return response.text
            
        except Exception as e:
            print(f"重试 {attempt+1}/3...")
            continue
    
    return None

# 使用
html = crawl('https://example.com')
```

### 示例2: 异步爬虫

```python
# async_spider.py
import aiohttp
from proxy_client import ProxyClient

client = ProxyClient()

async def fetch(session, url):
    """异步获取"""
    proxy = client.get_random()
    
    async with session.get(url, proxy=proxy) as response:
        return await response.text()

# 使用
async with aiohttp.ClientSession() as session:
    html = await fetch(session, 'https://example.com')
```

### 示例3: 代理池

```python
# proxy_pool.py
from proxy_client import ProxyClient
from queue import Queue

class ProxyPool:
    def __init__(self, size=10):
        self.client = ProxyClient()
        self.pool = Queue(maxsize=size)
        self.fill_pool()
    
    def fill_pool(self):
        """填充代理池"""
        proxies = self.client.get_best(limit=self.pool.maxsize)
        for proxy in proxies:
            self.pool.put(proxy)
    
    def get(self):
        """获取代理"""
        if self.pool.empty():
            self.fill_pool()
        return self.pool.get()
    
    def put_back(self, proxy):
        """归还代理"""
        if not self.pool.full():
            self.pool.put(proxy)

# 使用
pool = ProxyPool(size=20)
proxy = pool.get()
# ... 使用代理 ...
pool.put_back(proxy)
```

---

## 🔧 配置

### 修改端口

编辑 `proxy_api.py`:
```python
if __name__ == '__main__':
    run_api_server(port=8080)  # 改为其他端口
```

或使用环境变量:
```bash
set API_PORT=9000
python proxy_api.py
```

### 跨域访问

已启用CORS，支持跨域请求

---

## 📊 性能建议

### 1. 使用缓存

```python
class CachedProxyClient(ProxyClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache = []
        self._cache_time = 0
    
    def get_random(self):
        # 缓存5分钟
        if time.time() - self._cache_time > 300:
            self._cache = self.get_best(limit=50)
            self._cache_time = time.time()
        
        return random.choice(self._cache)
```

### 2. 连接池

```python
import requests
from requests.adapters import HTTPAdapter

session = requests.Session()
adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100)
session.mount('http://', adapter)

# 使用session而不是requests
```

---

## 🚨 常见问题

**Q: API服务器无法访问**
```bash
# 检查是否启动
curl http://localhost:8080/health

# 检查端口占用
netstat -ano | findstr :8080
```

**Q: 没有代理返回**
```bash
# 先运行扫描
python proxy_scanner_enhanced.py

# 检查数据库
python demo.py  # 选择选项2查看统计
```

**Q: 如何在后台运行**
```bash
# Windows
start /b python proxy_api.py

# Linux
nohup python proxy_api.py &
```

---

## ✅ 集成检查清单

- [ ] API服务器已启动
- [ ] 可以访问 http://localhost:8080
- [ ] 数据库有代理数据
- [ ] 在项目中安装了 requests
- [ ] 测试获取代理成功

---

**现在您可以在任何项目中使用代理了！** 🎉
