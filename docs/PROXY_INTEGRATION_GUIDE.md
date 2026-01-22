# 代理复用和集成方案

## 📋 三个核心问题的解决方案

### 1️⃣ 旧代理重新检测策略
### 2️⃣ 输出格式选择
### 3️⃣ 跨项目复用方案

---

## 1️⃣ 旧代理重新检测策略

### 方案A: 智能重新验证（推荐）⭐

**策略:**
- 每次扫描时，先验证数据库中的旧代理
- 根据历史表现决定是否保留
- 成功的继续使用，失败的移除或降级

**实现:**

```python
# proxy_scanner_enhanced.py 中添加

async def validate_existing_proxies(db, validator):
    """验证数据库中的现有代理"""
    
    # 获取最近24小时内的代理
    existing = db.get_all_active_proxies(hours=24)
    
    if not existing:
        logger.info("没有现有代理需要验证")
        return []
    
    logger.info(f"重新验证 {len(existing)} 个现有代理...")
    
    # 重新验证
    results = await validator.validate_proxies(existing)
    
    # 更新数据库
    for proxy_data in results:
        db.save_validation_result(proxy_data['proxy'], proxy_data)
    
    valid_count = len([r for r in results if r.get('is_valid')])
    logger.info(f"现有代理验证完成: {valid_count}/{len(existing)} 仍然有效")
    
    return results


# 在主函数中使用
async def main():
    # ... 初始化代码 ...
    
    # 1. 先验证旧代理
    existing_valid = await validate_existing_proxies(db, validator)
    
    # 2. 如果旧代理足够，跳过新扫描
    if len(existing_valid) >= 100:  # 阈值可配置
        logger.info(f"已有 {len(existing_valid)} 个有效代理，跳过新扫描")
        return
    
    # 3. 旧代理不足，获取新代理
    logger.info("现有代理不足，开始获取新代理...")
    # ... 正常扫描流程 ...
```

### 方案B: 定期全量验证

**策略:**
- 定时任务（如每小时）验证所有代理
- 标记失效的代理
- 保持代理池新鲜度

**实现:**

```python
# scheduled_validation.py

import schedule
import time

def validate_all_proxies():
    """验证所有代理"""
    db = ProxyDatabase()
    validator = ProxyValidator(config)
    
    all_proxies = db.get_all_active_proxies(hours=168)  # 一周内的
    # ... 验证逻辑 ...

# 每小时验证一次
schedule.every(1).hours.do(validate_all_proxies)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 方案C: 按需验证

**策略:**
- 只在使用时验证
- 使用前检查最后验证时间
- 超过阈值才重新验证

```python
def get_proxy_with_validation(db, max_age_minutes=30):
    """获取代理，如果太旧则重新验证"""
    proxy = db.get_best_proxies(limit=1)[0]
    
    # 检查最后验证时间
    if is_stale(proxy, max_age_minutes):
        # 重新验证
        result = validate_single(proxy['proxy_address'])
        db.save_validation_result(proxy['proxy_address'], result)
        return result if result['is_valid'] else None
    
    return proxy
```

### 🎯 推荐配置

```python
VALIDATION_CONFIG = {
    'mode': 'smart',  # smart | full | on-demand
    
    # 智能模式配置
    'smart': {
        'revalidate_existing': True,      # 每次扫描先验证旧代理
        'skip_scan_threshold': 100,       # 有足够旧代理就跳过新扫描
        'max_age_hours': 24,              # 只验证24小时内的旧代理
    },
    
    # 全量模式配置
    'full': {
        'schedule_hours': 1,              # 每小时全量验证
        'max_age_days': 7,                # 验证7天内的代理
    },
    
    # 按需模式配置
    'on_demand': {
        'max_age_minutes': 30,            # 超过30分钟才重新验证
    }
}
```

---

## 2️⃣ 输出格式选择

### 推荐的输出格式

#### 格式1: 纯文本列表（最通用）⭐

**用途:** 最简单，适合大多数工具

```text
# output/proxies.txt
1.2.3.4:1080
5.6.7.8:1080
9.10.11.12:1080
```

**优点:**
- ✅ 通用性最强
- ✅ 任何工具都能读取
- ✅ 一行一个代理

#### 格式2: JSON（详细信息）

**用途:** 需要额外信息（国家、评分等）

```json
// output/proxies.json
{
  "timestamp": "2026-01-22T13:24:00Z",
  "total": 150,
  "proxies": [
    {
      "address": "1.2.3.4:1080",
      "country": "US",
      "score": 85.5,
      "response_time": 1.23,
      "success_rate": 0.95
    }
  ]
}
```

#### 格式3: 按国家分类

**用途:** 需要按地区选择

```text
# output/proxies_by_country/
US.txt          # 美国代理
JP.txt          # 日本代理
DE.txt          # 德国代理
```

#### 格式4: API格式（直接调用）

**用途:** 其他项目HTTP调用

```bash
GET http://localhost:5000/api/proxy/random
# 返回随机一个代理

GET http://localhost:5000/api/proxy/best?country=US&limit=10
# 返回最佳代理
```

#### 格式5: 订阅格式（Clash/V2Ray）

**用途:** 代理工具订阅

```yaml
# output/clash.yaml
proxies:
  - name: "US-1"
    type: socks5
    server: 1.2.3.4
    port: 1080
```

### 🎯 推荐输出结构

```
output/
├── proxies.txt              # 纯文本（通用）⭐
├── proxies.json             # JSON（详细）
├── best_proxies.txt         # 最佳代理
├── by_country/              # 按国家分类
│   ├── US.txt
│   ├── JP.txt
│   └── ...
├── formats/                 # 各种格式
│   ├── clash.yaml
│   ├── v2ray.json
│   └── shadowrocket.conf
└── api_url.txt              # API地址
```

### 实现示例

```python
# exporters.py 扩展

class EnhancedExporter:
    
    async def export_all_formats(self, proxies):
        """导出所有格式"""
        
        # 1. 纯文本
        self.export_txt(proxies, 'output/proxies.txt')
        
        # 2. JSON详细
        self.export_json(proxies, 'output/proxies.json')
        
        # 3. 最佳代理
        best = sorted(proxies, key=lambda x: x['score'], reverse=True)[:50]
        self.export_txt(best, 'output/best_proxies.txt')
        
        # 4. 按国家分类
        self.export_by_country(proxies, 'output/by_country/')
        
        # 5. Clash格式
        self.export_clash(proxies, 'output/formats/clash.yaml')
    
    def export_by_country(self, proxies, output_dir):
        """按国家分类导出"""
        os.makedirs(output_dir, exist_ok=True)
        
        by_country = {}
        for proxy in proxies:
            country = proxy.get('country_code', 'XX')
            if country not in by_country:
                by_country[country] = []
            by_country[country].append(proxy['proxy'])
        
        for country, proxy_list in by_country.items():
            with open(f'{output_dir}/{country}.txt', 'w') as f:
                f.write('\n'.join(proxy_list))
```

---

## 3️⃣ 跨项目复用方案

### 方案A: 共享文件（简单）

**适合:** 同一台机器上的项目

```python
# 其他项目中
import random

def get_proxy():
    """从文件读取代理"""
    with open('/path/to/output/best_proxies.txt', 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]
    return random.choice(proxies) if proxies else None

# 使用
proxy = get_proxy()
# socks5://1.2.3.4:1080
```

### 方案B: HTTP API（推荐）⭐

**适合:** 任何项目，任何语言

#### 启动API服务器

```python
# proxy_api.py - 新建文件

from flask import Flask, jsonify, request
from proxy_database import ProxyDatabase
import random

app = Flask(__name__)
db = ProxyDatabase()

@app.route('/api/proxy/random')
def get_random_proxy():
    """获取随机代理"""
    proxies = db.get_best_proxies(limit=100)
    if not proxies:
        return jsonify({'error': 'No proxies available'}), 404
    
    proxy = random.choice(proxies)
    return jsonify({
        'address': proxy['proxy_address'],
        'country': proxy.get('country'),
        'score': proxy.get('avg_score'),
        'format': f"socks5://{proxy['proxy_address']}"
    })

@app.route('/api/proxy/best')
def get_best_proxies():
    """获取最佳代理列表"""
    limit = request.args.get('limit', 10, type=int)
    country = request.args.get('country')
    
    # TODO: 添加国家过滤
    proxies = db.get_best_proxies(limit=limit)
    
    return jsonify({
        'count': len(proxies),
        'proxies': [p['proxy_address'] for p in proxies]
    })

@app.route('/api/proxy/validate')
def validate_proxy():
    """验证代理是否可用"""
    proxy = request.args.get('proxy')
    stats = db.get_proxy_stats(proxy)
    
    return jsonify({
        'valid': stats is not None,
        'stats': stats
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

#### 其他项目调用

```python
# Python项目
import requests

def get_proxy():
    response = requests.get('http://localhost:8080/api/proxy/random')
    if response.status_code == 200:
        return response.json()['format']  # socks5://1.2.3.4:1080
    return None

# 使用
proxy = get_proxy()
session = requests.Session()
session.proxies = {'http': proxy, 'https': proxy}
```

```javascript
// Node.js项目
const axios = require('axios');

async function getProxy() {
    const response = await axios.get('http://localhost:8080/api/proxy/random');
    return response.data.format;
}

// 使用
const proxy = await getProxy();
```

### 方案C: SDK库（高级）

**适合:** 频繁使用的项目

```python
# proxy_client.py - SDK

class ProxyClient:
    """代理客户端SDK"""
    
    def __init__(self, api_url='http://localhost:8080'):
        self.api_url = api_url
        self._current_proxy = None
    
    def get_random(self):
        """获取随机代理"""
        response = requests.get(f'{self.api_url}/api/proxy/random')
        data = response.json()
        self._current_proxy = data['address']
        return data['format']
    
    def get_best(self, limit=10, country=None):
        """获取最佳代理列表"""
        params = {'limit': limit}
        if country:
            params['country'] = country
        
        response = requests.get(f'{self.api_url}/api/proxy/best', params=params)
        return response.json()['proxies']
    
    def with_retry(self, max_retries=3):
        """带重试的代理获取"""
        for _ in range(max_retries):
            proxy = self.get_random()
            if self.validate(proxy):
                return proxy
        return None
    
    def validate(self, proxy):
        """验证代理"""
        response = requests.get(
            f'{self.api_url}/api/proxy/validate',
            params={'proxy': proxy}
        )
        return response.json()['valid']

# 使用
client = ProxyClient()
proxy = client.get_random()
```

### 方案D: 共享数据库（高级用法）

**适合:** 多个项目，高性能需求

```python
# 其他项目直接访问数据库
from proxy_database import ProxyDatabase

db = ProxyDatabase('/path/to/proxies.db')
proxies = db.get_best_proxies(limit=10)
```

---

## 🎯 推荐方案组合

### 小型项目（1-2个项目）

```
方案: 共享文件
- 输出格式: proxies.txt
- 读取方式: 直接读文件
```

### 中型项目（3-5个项目）

```
方案: HTTP API
- 输出格式: JSON + TXT
- API服务: proxy_api.py
- 客户端: SDK库
```

### 大型项目（多语言、分布式）

```
方案: HTTP API + 数据库
- 输出格式: 全格式
- API服务: 高可用部署
- 数据库: 共享SQLite或PostgreSQL
```

---

## 📝 完整示例

### 场景: 在爬虫项目中使用

```python
# 爬虫项目 crawler.py

from proxy_client import ProxyClient
import requests

# 初始化代理客户端
proxy_client = ProxyClient('http://proxy-server:8080')

def crawl_with_proxy(url):
    """使用代理爬取"""
    for attempt in range(3):
        try:
            # 获取代理
            proxy = proxy_client.get_random()
            
            # 使用代理请求
            response = requests.get(
                url,
                proxies={'http': proxy, 'https': proxy},
                timeout=10
            )
            
            return response.text
            
        except Exception as e:
            print(f"代理失败，重试... ({attempt+1}/3)")
            continue
    
    return None

# 使用
html = crawl_with_proxy('https://example.com')
```

---

## ✅ 总结建议

### 问题1: 旧代理重新检测
**建议:** 采用智能重新验证（方案A）
- ✅ 每次扫描先验证旧代理
- ✅ 足够就跳过新扫描
- ✅ 节省资源，提高效率

### 问题2: 输出格式
**建议:** 多格式输出
- ✅ `proxies.txt` - 通用
- ✅ `proxies.json` - 详细信息
- ✅ `by_country/` - 按国家分类
- ✅ API接口 - 实时获取

### 问题3: 跨项目使用
**建议:** HTTP API + SDK
- ✅ 启动 `proxy_api.py` 提供API
- ✅ 其他项目用SDK调用
- ✅ 支持任何语言

---

**需要我立即实现这些功能吗？**
