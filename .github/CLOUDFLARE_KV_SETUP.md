# Cloudflare KV 配置指南

## 📋 前置要求

1. 拥有 Cloudflare 账户
2. 创建了 Workers KV Namespace
3. 获取了 API Token

---

## 🔧 配置步骤

### 1. 创建 KV Namespace

登录 Cloudflare Dashboard:
1. 进入 **Workers & Pages** → **KV**
2. 点击 **Create a namespace**
3. 命名为 `PROXY_POOL`
4. 记下 **Namespace ID** (类似：`1234567890abcdef1234567890abcdef`)

### 2. 创建 API Token

1. 进入 [API Tokens](https://dash.cloudflare.com/profile/api-tokens)
2. 点击 **Create Token**
3. 选择 **Custom token** 或使用模板
4. 设置权限：
   - **Account** → **Workers KV Storage** → **Edit**
5. 点击 **Continue to summary** → **Create Token**
6. **复制 Token**（只显示一次）

### 3. 获取 Account ID

1. 进入 Cloudflare Dashboard
2. 选择任意域名
3. 右侧边栏底部查看 **Account ID**
4. 复制该 ID

---

## 🔐 配置 GitHub Secrets

进入 GitHub 仓库：`Settings` → `Secrets and variables` → `Actions`

点击 **New repository secret**，添加以下变量：

### 必需变量

| Secret 名称 | 值 | 说明 |
|------------|-----|------|
| `CLOUDFLARE_API_TOKEN` | `your_api_token_here` | 从步骤 2 获取 |
| `CLOUDFLARE_ACCOUNT_ID` | `your_account_id_here` | 从步骤 3 获取 |
| `KV_NAMESPACE_ID` | `1234567890abcdef...` | 从步骤 1 获取 |

### 可选变量（Telegram 通知）

| Secret 名称 | 值 | 说明 |
|------------|-----|------|
| `TELEGRAM_BOT_TOKEN` | `123456:ABC-DEF...` | 从 @BotFather 获取 |
| `TELEGRAM_CHAT_ID` | `123456789` | 从 @userinfobot 获取 |

---

## ✅ 测试配置

1. 推送代码到 GitHub
2. 进入 **Actions** 标签
3. 选择 **代理池自动更新并同步到 Cloudflare KV**
4. 点击 **Run workflow**
5. 等待运行完成

---

## 🔍 验证数据

### 方法 1: 通过 Cloudflare Dashboard
1. 进入 **Workers & Pages** → **KV**
2. 点击 `PROXY_POOL` namespace
3. 查看键名 `current_proxies` 的值

### 方法 2: 通过 API
```bash
curl "https://api.cloudflare.com/client/v4/accounts/YOUR_ACCOUNT_ID/storage/kv/namespaces/YOUR_NAMESPACE_ID/values/current_proxies" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

### 方法 3: 通过 Workers
创建一个 Cloudflare Worker:
```javascript
export default {
  async fetch(request, env) {
    const data = await env.PROXY_POOL.get('current_proxies', 'json');
    return new Response(JSON.stringify(data, null, 2), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
```

---

## 📖 使用 KV 数据

### 在 Cloudflare Worker 中读取
```javascript
export default {
  async fetch(request, env) {
    // 读取代理列表
    const proxies = await env.PROXY_POOL.get('current_proxies', 'json');
    
    if (!proxies || !proxies.proxies || proxies.proxies.length === 0) {
      return new Response('No proxies available', { status: 404 });
    }
    
    // 随机选择一个代理
    const randomProxy = proxies.proxies[
      Math.floor(Math.random() * proxies.proxies.length)
    ];
    
    return new Response(JSON.stringify({
      proxy: `${randomProxy.ip}:${randomProxy.port}`,
      protocol: randomProxy.protocol,
      country: randomProxy.country,
      latency: randomProxy.latency,
      total_available: proxies.metadata.total,
      last_updated: proxies.metadata.updated_at
    }, null, 2), {
      headers: { 
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
  }
}
```

---

## 🛠️ 故障排查

### 问题 1: 上传失败 (401 Unauthorized)
**原因:** API Token 无效或权限不足  
**解决:**
- 检查 `CLOUDFLARE_API_TOKEN` 是否正确
- 确认 Token 有 **Workers KV:Edit** 权限
- 重新创建 Token

### 问题 2: 上传失败 (404 Not Found)
**原因:** Namespace ID 或 Account ID 错误  
**解决:**
- 检查 `KV_NAMESPACE_ID` 是否正确
- 检查 `CLOUDFLARE_ACCOUNT_ID` 是否正确

### 问题 3: proxies.json 不存在
**原因:** 扫描器未生成文件  
**解决:**
- 查看 Actions 日志
- 检查 Python 依赖是否安装成功
- 本地测试 `python proxy_scanner_enhanced.py`

---

## 📊 监控和日志

**GitHub Actions 日志:**
- 进入仓库 **Actions** 标签
- 选择运行记录查看详细日志

**Cloudflare KV 使用情况:**
- Cloudflare Dashboard → **Workers & Pages** → **KV**
- 查看 Namespace 的读写统计

---

**配置完成！** 🎉

每 6 小时，GitHub Actions 会自动扫描代理并同步到 Cloudflare KV。
