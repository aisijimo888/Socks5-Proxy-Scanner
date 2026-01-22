# 订阅链接使用示例

## 🚀 快速开始 - 3步配置

### 方法 1：使用 GitHub 订阅链接（推荐）⭐

**优点：** 无需运行任何服务，自动更新，永久可用

#### 步骤 1：获取你的订阅链接
将下面的链接中的 `你的用户名` 和 `仓库名` 替换为实际值：

```
Clash:
https://raw.githubusercontent.com/你的用户名/仓库名/main/subscribe/clash.yaml

V2Ray:
https://raw.githubusercontent.com/你的用户名/仓库名/main/subscribe/v2ray.json

ShadowRocket:
https://raw.githubusercontent.com/你的用户名/仓库名/main/subscribe/shadowrocket.txt
```

#### 步骤 2：导入到客户端

**Clash 用户：**
1. 打开 Clash → 配置 → 添加
2. 粘贴 Clash 订阅链接
3. 点击更新订阅
4. ✅ 完成！

**V2RayN 用户（Windows）：**
1. 打开 V2RayN → 订阅 → 订阅设置
2. 点击添加 → 粘贴 V2Ray 订阅链接
3. 确定 → 更新订阅
4. ✅ 完成！

**ShadowRocket 用户（iOS）：**
1. 打开 ShadowRocket → 右上角 +
2. Subscribe → 粘贴 ShadowRocket 订阅链接
3. 完成
4. ✅ 完成！

#### 步骤 3：享受自动更新
- GitHub Actions 每6小时自动更新代理池
- 你的客户端会自动获取最新代理
- 无需任何手动操作！

---

### 方法 2：通过 API 服务器

**适用场景：** 需要本地控制或自定义筛选条件

#### 步骤 1：启动 API 服务器
```bash
python proxy_api.py
```

服务器运行在 `http://localhost:8080`

#### 步骤 2：使用本地订阅链接
```
Clash:
http://localhost:8080/api/subscribe/clash

V2Ray:
http://localhost:8080/api/subscribe/v2ray

Base64:
http://localhost:8080/api/subscribe/base64
```

#### 步骤 3：配置客户端
与方法1相同，只是使用本地链接。

---

## 📱 客户端详细配置

### Clash for Windows

1. **添加订阅**
   - 点击 `Profiles`
   - 在输入框粘贴订阅链接
   - 点击 `Download`

2. **选择配置**
   - 下载完成后，配置会出现在列表中
   - 点击配置名称即可激活

3. **更新订阅**
   - 右键配置 → `Update`
   - 或设置自动更新间隔

### V2RayN (Windows)

1. **添加订阅**
   ```
   订阅 → 订阅设置 → 添加订阅
   地址：粘贴订阅链接
   备注：随便填（例如：我的代理池）
   ```

2. **更新订阅**
   ```
   订阅 → 更新订阅
   ```

3. **选择节点**
   - 主界面会显示所有代理
   - 双击或右键 → 设为活动服务器

### V2RayNG (Android)

1. **添加订阅**
   ```
   右上角 ⋮ → 订阅设置
   点击 + → 输入订阅地址
   ```

2. **更新订阅**
   ```
   右上角 ⋮ → 更新订阅
   ```

### ShadowRocket (iOS)

1. **添加订阅**
   ```
   首页 → 右上角 + → 类型选择 Subscribe
   URL：粘贴订阅链接
   备注：我的代理池
   ```

2. **更新订阅**
   - 下拉刷新即可更新

---

## 🔧 高级用法

### 通过 API 获取特定国家的代理

```bash
# 获取美国代理
curl "http://localhost:8080/api/proxy/best?country=US&limit=50"

# 获取日本代理
curl "http://localhost:8080/api/proxy/best?country=JP&limit=50"
```

### 编程方式使用

**Python 示例：**
```python
import requests

# 获取随机代理
response = requests.get('http://localhost:8080/api/proxy/random')
proxy_info = response.json()

# 使用代理
proxies = {
    'http': proxy_info['format'],   # socks5://1.2.3.4:1080
    'https': proxy_info['format']
}

# 发送请求
result = requests.get('https://httpbin.org/ip', proxies=proxies)
print(result.json())
```

**JavaScript 示例：**
```javascript
// 获取最佳代理列表
fetch('http://localhost:8080/api/proxy/best?limit=10')
  .then(response => response.json())
  .then(data => {
    console.log('可用代理：', data.proxies);
  });
```

---

## ❓ 常见问题

### Q1: 订阅链接无法访问？
**A:** 确保：
- GitHub Actions 已运行过至少一次
- `subscribe/` 目录中有订阅文件
- 链接中的用户名和仓库名正确

### Q2: 代理连接不上？
**A:** 代理可能失效，建议：
- 更新订阅（客户端会获取最新代理）
- GitHub Actions 每6小时自动验证和更新

### Q3: 如何查看代理质量？
**A:** 
```bash
# 查看统计信息
curl http://localhost:8080/api/stats

# 或访问 Web Dashboard
python web_dashboard.py
# 打开 http://localhost:5000
```

### Q4: 想要更多代理？
**A:** 修改 `subscription_generator.py` 中的参数：
```python
# 增加代理数量限制
generator.generate_all_formats(limit=500, min_score=0.5)
```

---

## 🎯 推荐配置

### 日常使用
- 使用 GitHub 订阅链接
- 客户端设置自动更新（每天1次）
- 选择自动测速或故障转移模式

### 开发测试
- 运行本地 API 服务器
- 使用 API 端点动态获取
- 根据项目需求筛选代理

### 企业部署
- 部署 API 服务器到内网
- 配置定时任务更新代理池
- 通过内网订阅链接分发

---

**享受便捷的代理订阅服务！** 🚀
