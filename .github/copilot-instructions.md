# 快速上手（AI 编码代理指南）

本仓库包含工业级 SOCKS5 代理采集、校验、转换工具。AI 代理应理解三层架构和多维评分体系。

## 核心架构

| 组件 | 职责 | 输入 | 输出 |
|------|------|------|------|
| \socks5.py\ | 多源采集 + 三层过滤验证 + 评分 | 20+ GitHub 源 + 公开网站 | \Industrial_Socks5_*.txt\ |
| \clash-socks5.py\ | 文本转 Clash YAML | \Industrial_Socks5.txt\ | \clash_socks5.yaml\ |
| \国际家宽验证器.py\ | 混合协议真测（SOCKS5/SS/VLESS/Trojan） | Clash YAML 节点 | 验证结果 |

## 三层过滤管道（socks5.py）

1. **本地 GeoIP 快筛** (\ilter_by_local_geoip\)：读 \GeoLite2-ASN.mmdb\，过滤国家/ASN（机房关键词 \BAD_ASN_KEYWORDS\）
2. **DNSBL 黑名单检测** (\check_dnsbl\)：DNS 查询 \zen.spamhaus.org\，去除垃圾邮件 IP
3. **API 真实验证** (\alidate_node\)：HTTP 请求 \ip-api.com/json/\，采样 \mobile\/\hosting\ 字段，计算评分

## 配置与评分体系

- **配置中心** \config.py\：\BAD_ASN_KEYWORDS\、\TARGET_COUNTRIES\、\USE_LOCAL_DB\、\ENABLE_DNSBL\、\FOFA_CACHE_FILE\
- **评分逻辑** \IndustrialCleaner.score_candidate()\：
  - 基础：1.0
  - ISP 类型（非机房）：+0.0（过滤）
  - 目标国家：+1.8（\COUNTRY_MOBILE_REWARD\）
  - 住宅/手机：+1.8
  - 常见代理端口：+1.0（\PORT_REWARD\）
- **过滤模式** 三种策略：
  - \strict\：评分  2.8，仅接受高分节点
  - \alanced\：评分  1.0，默认模式
  - \lenient\：评分  0.5，宽松过滤

## 关键代码位置

- **采集循环**（第 270-350 行）：\etch_sources()\ + \etch_from_public_sites()\，使用 \	qdm_asyncio\ 显示进度
- **验证单节点**（第 500+ 行）：\alidate_node()\，调用 \ip-api.com\，建立缓存 session
- **并发管理**（第 210-220 行）：\Semaphore(10)\ 限制 DNS、\Semaphore(MAX_CONCURRENCY)\ 限制 HTTP
- **Clash 节点构造**（\clash-socks5.py\ 第 30-40 行）：字典 \{name, type: socks5, server, port, skip-cert-verify: true}\

## 运行命令与参数

\\\ash
# 基础采集（balanced 模式）
python socks5.py

# 指定过滤模式与评分阈值
python socks5.py --filter-mode strict --score-threshold 2.5

# 覆盖并发与奖励
python socks5.py --max-concurrency 50 --port-reward 1.5 --country-mobile-reward 2.0

# 转换为 Clash YAML
python clash-socks5.py

# 混合协议验证（读 Clash 配置，真测）
python 国际家宽验证器.py
\\\

## 项目特定模式

1. **长寿命 Session 复用**：\_init_sessions()\ 在 \un()\ 开始创建 \ip_info_session\、\connectivity_session\，避免反复 TLS 握手
2. **ProxyConnector 缓存**：按 \ip:port\ 存于 \proxy_connector_cache{}\，限制容量 \Semaphore(10)\
3. **异步信号量分离**：DNS 用一个，HTTP 验证用另一个，灵活扩展
4. **中文 emoji 输出**：\EMOJI_ENABLED\ 因 Windows 默认禁用；保留中文注释和符号有助于运维可观测性
5. **错误恢复**：网络请求 3 次重试，间隔指数增长；验证失败计入 \ailure_rate\，自动调整 \MAX_CONCURRENCY\

## 外部依赖与速率限制

- **ip-api.com**：45 req/min（注意速率限制，错误代码 429）
- **Spamhaus DNSBL**：无官方限制，但通常 ISP 限制同时连接数（使用 \Semaphore(10)\ 防护）
- **GitHub raw.githubusercontent.com**：60 req/hr 未认证；支持 \--fofa-cache-file\ 降低 FOFA API 调用
- **GeoLite2-ASN.mmdb**：需手动下载（\geoip2\ 库读取），校验 MD5 避免损坏

## 修改指南

- **新增数据源**：编辑 \SOURCES\ 列表，格式需为 \ip:port\ 纯文本或 API 直连格式
- **调整过滤**：优先改 \config.py\ 或命令行参数，避免改 \socks5.py\ 内嵌常量
- **替换验证 API**：修改 \alidate_node()\ 调用的 URL，需支持异步；确保返回 JSON 包含 \countryCode\、\mobile\、\hosting\ 字段
- **新增协议**：参考 \MixedChecker.process_node()\ 的 dict/str 分流模式，按 \
ode['type']\ 路由
- **性能优化**：调整 \iohttp.ClientTimeout\ 常量、\MAX_CONCURRENCY\、\DNSBL_ZONES\ 列表规模
