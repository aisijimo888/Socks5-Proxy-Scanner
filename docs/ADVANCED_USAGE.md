# SOCKS5代理扫描器 - 高级使用指南

本文档介绍高级功能和最佳实践。

## 目录
- [数据库高级查询](#数据库高级查询)
- [自定义评分规则](#自定义评分规则)
- [API集成示例](#api集成示例)
- [性能调优](#性能调优)
- [生产环境部署](#生产环境部署)

## 数据库高级查询

### 复杂查询示例

```python
from proxy_database import ProxyDatabase
import sqlite3

db = ProxyDatabase()

# 获取特定国家的高质量代理
with db._get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            p.proxy_address,
            p.country,
            AVG(vh.score) as avg_score,
            COUNT(vh.id) as checks
        FROM proxies p
        INNER JOIN validation_history vh ON p.id = vh.proxy_id
        WHERE 
            p.country IN ('United States', 'Germany', 'Japan')
            AND vh.is_valid = 1
        GROUP BY p.id
        HAVING checks >= 5 AND avg_score >= 70
        ORDER BY avg_score DESC
        LIMIT 20
    """)
    results = cursor.fetchall()
```

### 时间序列分析

```python
# 分析代理成功率趋势
cursor.execute("""
    SELECT 
        DATE(timestamp) as date,
        COUNT(*) as total_checks,
        SUM(CASE WHEN is_valid THEN 1 ELSE 0 END) as valid_checks,
        AVG(response_time) as avg_response_time
    FROM validation_history
    WHERE timestamp >= datetime('now', '-7 days')
    GROUP BY DATE(timestamp)
    ORDER BY date
""")
```

### 代理池健康监控

```python
def get_pool_health_metrics(db):
    """获取代理池健康指标"""
    stats = db.get_database_stats()
    
    metrics = {
        'health_score': 0,
        'warnings': [],
        'recommendations': []
    }
    
    # 检查活跃代理比例
    if stats['total_proxies'] > 0:
        active_ratio = stats['active_proxies_24h'] / stats['total_proxies']
        if active_ratio < 0.3:
            metrics['warnings'].append('活跃代理比例过低')
            metrics['recommendations'].append('建议运行新的扫描')
    
    # 检查成功率
    if stats['success_rate_24h'] < 0.5:
        metrics['warnings'].append('成功率低于50%')
        metrics['recommendations'].append('检查网络连接或代理源质量')
    
    # 计算健康评分
    metrics['health_score'] = (
        active_ratio * 50 + 
        stats['success_rate_24h'] * 50
    )
    
    return metrics
```

## 自定义评分规则

### 创建自定义评分器

```python
from enhanced_validator import ProxyScorer

class CustomScorer(ProxyScorer):
    """自定义评分器"""
    
    def calculate_score(self, proxy_data, historical_stats=None):
        """自定义评分逻辑"""
        score = 0
        
        # 1. 响应时间评分 (40分)
        response_time = proxy_data.get('response_time', 999)
        if response_time < 0.5:
            score += 40
        elif response_time < 1:
            score += 35
        elif response_time < 2:
            score += 25
        elif response_time < 5:
            score += 15
        
        # 2. 地理位置评分 (30分)
        country = proxy_data.get('country', '')
        if 'United States' in country:
            score += 30
        elif 'Japan' in country or 'Germany' in country:
            score += 25
        elif country:
            score += 15
        
        # 3. 稳定性评分 (30分)
        if historical_stats:
            success_rate = historical_stats.get('success_rate', 0)
            total_checks = historical_stats.get('total_checks', 0)
            
            # 成功率权重
            score += success_rate * 20
            
            # 检查次数奖励
            if total_checks >= 20:
                score += 10
            elif total_checks >= 10:
                score += 5
        
        return min(score, 100)
```

### 使用自定义评分器

```python
# 在主扫描器中使用
scorer = CustomScorer(db)
for proxy_data in valid_proxies:
    score = scorer.calculate_score(proxy_data, historical_stats)
    proxy_data['score'] = score
```

## API集成示例

### Flask API扩展

```python
from flask import Flask, request, jsonify
from proxy_database import ProxyDatabase

app = Flask(__name__)
db = ProxyDatabase()

@app.route('/api/v2/proxies/filter', methods=['POST'])
def filter_proxies():
    """高级过滤接口"""
    filters = request.json
    
    min_score = filters.get('min_score', 60)
    countries = filters.get('countries', [])
    max_response_time = filters.get('max_response_time', 5)
    
    with db._get_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT p.*, AVG(vh.score) as score
            FROM proxies p
            INNER JOIN validation_history vh ON p.id = vh.proxy_id
            WHERE vh.is_valid = 1
        """
        
        params = []
        
        if countries:
            placeholders = ','.join(['?' for _ in countries])
            query += f" AND p.country IN ({placeholders})"
            params.extend(countries)
        
        query += " GROUP BY p.id HAVING score >= ?"
        params.append(min_score)
        
        query += " ORDER BY score DESC LIMIT 100"
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
    
    return jsonify({
        'success': True,
        'count': len(results),
        'proxies': results
    })

@app.route('/api/v2/analytics/timeline', methods='GET'])
def get_timeline():
    """获取时间线数据"""
    days = request.args.get('days', 7, type=int)
    
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(DISTINCT proxy_id) as unique_proxies,
                AVG(response_time) as avg_response_time,
                SUM(CASE WHEN is_valid THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
            FROM validation_history
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (days,))
        
        results = [dict(row) for row in cursor.fetchall()]
    
    return jsonify({
        'success': True,
        'data': results
    })
```

### Python SDK示例

```python
import requests

class ProxyPoolClient:
    """代理池API客户端"""
    
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
    
    def get_proxies(self, limit=10, min_score=60):
        """获取代理列表"""
        response = requests.get(
            f'{self.base_url}/api/proxies',
            params={'limit': limit, 'min_success_rate': min_score/100}
        )
        return response.json()
    
    def get_random_proxy(self):
        """获取随机代理"""
        proxies = self.get_proxies(limit=1)
        if proxies['success'] and proxies['data']:
            return proxies['data'][0]['proxy_address']
        return None
    
    def check_proxy_status(self, proxy_address):
        """检查代理状态"""
        response = requests.get(
            f'{self.base_url}/api/proxy/{proxy_address}'
        )
        return response.json()

# 使用示例
client = ProxyPoolClient()
proxy = client.get_random_proxy()
print(f"获取到代理: {proxy}")
```

## 性能调优

### 并发优化

```python
# 根据系统资源调整并发数
import psutil

def get_optimal_concurrency():
    """计算最优并发数"""
    cpu_count = psutil.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    # 基于CPU核心数
    base_concurrency = cpu_count * 10
    
    # 基于内存调整
    if memory_gb < 2:
        base_concurrency = min(base_concurrency, 30)
    elif memory_gb < 4:
        base_concurrency = min(base_concurrency, 50)
    else:
        base_concurrency = min(base_concurrency, 100)
    
    return base_concurrency

# 使用
optimal = get_optimal_concurrency()
print(f"推荐并发数: {optimal}")
```

### 数据库优化

```python
# 创建额外索引
def optimize_database(db):
    """优化数据库性能"""
    with db._get_connection() as conn:
        cursor = conn.cursor()
        
        # 创建复合索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_proxy_country_score 
            ON proxies(country, last_seen)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_validation_valid_time
            ON validation_history(is_valid, timestamp)
        """)
        
        # 分析表以优化查询计划
        cursor.execute("ANALYZE")
        
        print("数据库优化完成")
```

### 内存管理

```python
# 批量处理大量代理
def process_proxies_in_batches(proxies, batch_size=1000):
    """批量处理避免内存溢出"""
    for i in range(0, len(proxies), batch_size):
        batch = proxies[i:i+batch_size]
        # 处理批次
        yield batch

# 使用
for batch in process_proxies_in_batches(all_proxies):
    results = await validator.validate_batch(batch)
    # 处理结果
```

## 生产环境部署

### Docker部署

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "web_dashboard.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  scanner:
    build: .
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_PATH=/app/data/proxies.db
    command: python proxy_scanner_enhanced.py --db-path /app/data/proxies.db
  
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_PATH=/app/data/proxies.db
      - WEB_PORT=5000
    depends_on:
      - scanner
```

### Systemd服务

```ini
# /etc/systemd/system/proxy-dashboard.service
[Unit]
Description=SOCKS5 Proxy Dashboard
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/proxy-scanner
Environment="PATH=/opt/proxy-scanner/venv/bin"
ExecStart=/opt/proxy-scanner/venv/bin/python web_dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Nginx反向代理

```nginx
server {
    listen 80;
    server_name proxies.example.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 监控和日志

```python
# 集成Prometheus监控
from prometheus_client import Counter, Histogram, Gauge
from flask import Flask

proxy_validation_total = Counter(
    'proxy_validation_total',
    'Total proxy validations'
)

proxy_validation_duration = Histogram(
    'proxy_validation_duration_seconds', 
    'Proxy validation duration'
)

active_proxies_gauge = Gauge(
    'active_proxies_count',
    'Number of active proxies'
)

@app.route('/metrics')
def metrics():
    from prometheus_client import generate_latest
    return generate_latest()
```

## 最佳实践

1. **定期备份数据库**
   ```bash
   sqlite3 proxies.db ".backup 'backup/proxies_$(date +%Y%m%d).db'"
   ```

2. **监控代理池健康度**
   - 设置成功率阈值告警
   - 监控活跃代理数量
   - 定期检查源状态

3. **优化扫描策略**
   - 高峰时段降低并发
   - 分时段扫描不同源
   - 优先验证历史高质量代理

4. **安全建议**
   - 不要暴露数据库文件
   - Web Dashboard使用HTTPS
   - API添加认证机制
   - 限制请求频率

---

更多问题请查看主README或提交Issue。
