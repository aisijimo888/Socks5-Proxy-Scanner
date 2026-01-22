# -*- coding: utf-8 -*-
# 文件名: Industrial_Socks5_Engine.py
# 新增特性：本地GeoIP过滤 | Spamhaus黑名单检测 | 目标国家筛选

import sys
import io
# 强制 stdout 使用 UTF-8 编码（防止 emoji 乱码）
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
# 同时强制 stdout 和 stderr 使用 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
import re
import argparse
import os
import dns.resolver  # 需要 pip install dnspython
import geoip2.database # 需要 pip install geoip2
import logging
import platform

# ================== 高级配置 ===================
SOURCES = [
    # 主流高质量源（高覆盖面）
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks5.txt",
    "https://www.proxy-list.download/api/v1/get?type=socks5",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    
    # CDN加速备用（绕过 GitHub 限流）
    "https://cdn.jsdelivr.net/gh/monosans/proxy-list@main/proxies/socks5.txt",
    "https://cdn.jsdelivr.net/gh/rdavydov/proxy-list@main/proxies/socks5.txt",
    "https://cdn.jsdelivr.net/gh/sunny9577/proxy-scraper@main/proxies.txt",
    "https://cdn.jsdelivr.net/gh/ShiftyTR/Proxy-List@master/socks5.txt",
    
    # 中等知名度源（中等竞争）
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
    "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks5.txt",
    
    # 低竞争度小众源（被爬取人数较少）
    "https://raw.githubusercontent.com/calclavia/proxy-list/master/proxies.txt",
    "https://raw.githubusercontent.com/opsxcq/proxy-list/master/https.txt",
    "https://raw.githubusercontent.com/almroot/proxylist/master/socks5.txt",
    "https://raw.githubusercontent.com/pteod/proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/nanachi-code/proxy-list/main/text/socks5.txt",
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks5.txt",
    "https://raw.githubusercontent.com/Zaeem20/proxy_scraper/master/proxies.txt",
    "https://raw.githubusercontent.com/officialcedricbahire/proxy-list/main/proxies.txt",
    "https://raw.githubusercontent.com/aslisk/proxylist/main/socks5.txt",
    "https://raw.githubusercontent.com/Anonym0usss/proxy_scraper/main/proxies.txt",
    "https://raw.githubusercontent.com/proxifly/proxylist/main/socks5.txt",
    
    # 极冷门源（活跃但几乎无人爬取）
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/socks5.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/master/SOCKS5_RAW.txt",
    "https://raw.githubusercontent.com/QuantumVortex/proxy-list/master/socks5.txt",
    "https://raw.githubusercontent.com/UserR3X/proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/Tolar-HashNET/TNCM-Socks5-Proxy-List/main/SOCKS5.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxylist.txt",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-LIST/master/socks5.txt",
    "https://raw.githubusercontent.com/vonsylvia/proxy-list/master/socks5.txt",
    "https://raw.githubusercontent.com/yuceltoluyag/Proxy-Lists/master/socks5.txt",
    "https://raw.githubusercontent.com/xiaojingbin/socks5_proxy/main/proxy.txt",
    
    # 国内爬虫社区源（国内用户多但国外用户少）
    "https://raw.githubusercontent.com/jia-sai/proxy-pool/master/proxies.txt",
    "https://raw.githubusercontent.com/Licoy/proxy_pool/main/src/data/proxy.txt",
    "https://raw.githubusercontent.com/Uukenn/ProxyList/master/socks5.txt",
    
    # 备用 CDN 线路（超低竞争，仅备用）
    "https://cdn.jsdelivr.net/gh/mertguvencli/http-proxy-list@main/socks5.txt",
    "https://cdn.jsdelivr.net/gh/zevtyardt/proxy-list@main/socks5.txt",
]

# 公开代理网站列表（无需注册，通过 HTML 爬取 ip:port）
PUBLIC_PROXY_SITES = [
    {
        "url": "https://www.free-proxy-list.net/",
        "name": "free-proxy-list.net",
        "parser": "table",
    },
    {
        "url": "https://www.socks-proxy.net/",
        "name": "socks-proxy.net",
        "parser": "table",
    },
    {
        "url": "https://free-proxy-list.net/socks5.html",
        "name": "free-proxy-list socks5",
        "parser": "table",
    },
    {
        "url": "https://www.us-proxy.org/",
        "name": "us-proxy.org",
        "parser": "table",
    },
    {
        "url": "https://free-proxy-list.net/uk-proxy.html",
        "name": "free-proxy-list uk",
        "parser": "table",
    },
]

# 1. 目标国家 (空列表代表不限制)
TARGET_COUNTRIES = ["US", "HK", "SG", "JP", "GB"] 

# 2. 本地数据库路径 (建议下载 GeoLite2-ASN.mmdb 以获得极致速度)
# 如果没有文件，请将 Use_Local_DB 设为 False
USE_LOCAL_DB = True 
MMDB_PATH = "GeoLite2-ASN.mmdb"

# 3. 开启 DNSBL 黑名单检测 (过滤掉被标记为垃圾邮件/僵尸网络的IP)
ENABLE_DNSBL = True
# 4. 常见的机房 ASN 关键词 (本地库过滤用)
# 尝试从可选的 config.py 加载覆盖项，否则使用上面定义的默认值
try:
    import config as _config
    BAD_ASN_KEYWORDS = getattr(_config, 'BAD_ASN_KEYWORDS', [])
    TARGET_COUNTRIES = getattr(_config, 'TARGET_COUNTRIES', TARGET_COUNTRIES)
    USE_LOCAL_DB = getattr(_config, 'USE_LOCAL_DB', USE_LOCAL_DB)
    MMDB_PATH = getattr(_config, 'MMDB_PATH', MMDB_PATH)
    ENABLE_DNSBL = getattr(_config, 'ENABLE_DNSBL', ENABLE_DNSBL)
    FOFA_CACHE_FILE = getattr(_config, 'FOFA_CACHE_FILE', 'fofa_cache.txt')
except Exception:
    # config.py 可选：未提供时使用文件顶部定义的默认值
    BAD_ASN_KEYWORDS = []
    FOFA_CACHE_FILE = 'fofa_cache.txt'

# 默认评分奖励/惩罚（可由命令行覆盖）
DEFAULT_PORT_REWARD = 1.0
DEFAULT_COUNTRY_MOBILE_REWARD = 1.8
# 过滤模式：'strict' | 'balanced' | 'lenient'
FILTER_MODE = 'strict'

# 命令行解析之前，基于平台决定是否显示 emoji（Windows PowerShell 5.1 常见乱码）
EMOJI_ENABLED = False if platform.system() == 'Windows' else True

# 运行时可被命令行覆盖的变量（先定义默认值以防 NameError）
PORT_REWARD = DEFAULT_PORT_REWARD
COUNTRY_MOBILE_REWARD = DEFAULT_COUNTRY_MOBILE_REWARD
GLOBAL_SCORE_THRESHOLD = 1.0
# 并发控制（可通过命令行覆盖）
MAX_CONCURRENCY = 60
# DNSBL 黑名单服务列表（多源降低单点故障风险）
DNSBL_ZONES = [
    'zen.spamhaus.org',
    'b.barracudacentral.org',
    'bl.spamcop.net',
]
# ===============================================

def load_sources_from_file(file_path):
    """从本地文件加载额外的代理源，每行一个URL"""
    global SOURCES
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    s = line.strip()
                    if s and s not in SOURCES:
                        SOURCES.append(s)
            logging.info('Loaded extra sources from %s (total sources: %s)', file_path, len(SOURCES))
        except Exception as e:
            logging.warning('Failed to read sources-file %s: %s', file_path, e)
    else:
        logging.warning('sources-file not found: %s', file_path)

class IndustrialCleaner:
    def __init__(self):
        self.raw_proxies = set()
        self.clean_proxies = []
        self.reader = None
        self.fetch_connector = None
        self.logger = logging.getLogger(__name__)
        if USE_LOCAL_DB:
            try:
                self.reader = geoip2.database.Reader(MMDB_PATH)
                print(("✅ " if EMOJI_ENABLED else "") + "本地 GeoIP 数据库已加载")
            except Exception as e:
                self.logger.debug('GeoIP load failed: %s', e)
                print(("⚠️ " if EMOJI_ENABLED else "") + "未找到 .mmdb 文件，已降级为仅在线检测")

    async def fetch_sources(self):
        # 增强：添加 User-Agent、重试、状态码与内容长度日志，便于诊断“0 个原始 IP”问题
        headers = {"User-Agent": "Mozilla/5.0 (compatible; IndustrialCleaner/1.0)"}
        async with aiohttp.ClientSession(headers=headers, connector=self.fetch_connector) as session:
            for url in SOURCES:
                success = False
                for attempt in range(1, 4):
                    try:
                        async with session.get(url, timeout=10) as resp:
                            status = resp.status
                            text = await resp.text()
                            length = len(text) if text else 0
                            self.logger.info("fetched %s -> status=%s length=%s (attempt %s)", url, status, length, attempt)
                            if status == 200 and length > 0:
                                found = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b', text)
                                self.raw_proxies.update(found)
                                success = True
                                break
                            else:
                                # 非 200 或空内容，等待后重试
                                await asyncio.sleep(attempt)  # 线性 backoff
                    except Exception as e:
                        self.logger.debug("fetch_sources exception for %s (attempt %s): %s", url, attempt, e)
                        await asyncio.sleep(attempt)

                # 删除以下重复或低价值的日志记录
                # self.logger.warning("failed to fetch or parse %s after retries", url)
        print(("📥 " if EMOJI_ENABLED else "") + f"采集完成，共 {len(self.raw_proxies)} 个原始 IP")

    async def fetch_from_public_sites(self):
        """
        从公开代理网站（无需注册）抓取 ip:port。
        使用 beautifulsoup4 解析 HTML 表格。
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            self.logger.warning('beautifulsoup4 not installed, skipping public site scraping')
            return

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        async with aiohttp.ClientSession(headers=headers, connector=self.fetch_connector) as session:
            for site_config in PUBLIC_PROXY_SITES:
                url = site_config.get('url')
                name = site_config.get('name')
                if not url:
                    continue

                try:
                    async with session.get(url, timeout=15, ssl=False) as resp:
                        if resp.status != 200:
                            self.logger.debug(f'public site {name} returned status {resp.status}')
                            continue

                        html = await resp.text()
                        # 尝试用 BeautifulSoup 解析 HTML 表格
                        soup = BeautifulSoup(html, 'html.parser')
                        table = soup.find('table')
                        if not table:
                            # 也尝试正则提取 ip:port
                            found = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b", html)
                            for ip_port in found:
                                if ip_port not in self.raw_proxies:
                                    self.raw_proxies.add(ip_port)
                            if found:
                                self.logger.info(f'public site {name}: found {len(found)} ips by regex')
                            continue

                        rows = table.find_all('tr')
                        found_count = 0
                        for row in rows[1:]:  # 跳过表头
                            cols = row.find_all('td')
                            if len(cols) >= 2:
                                # 第一列通常是 IP，第二列是端口
                                ip = cols[0].text.strip()
                                port_text = cols[1].text.strip()
                                if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip) and port_text.isdigit():
                                    ip_port = f"{ip}:{port_text}"
                                    if ip_port not in self.raw_proxies:
                                        self.raw_proxies.add(ip_port)
                                        found_count += 1

                        self.logger.info(f'public site {name}: extracted {found_count} new proxies')
                except Exception as e:
                    self.logger.debug(f'fetch_from_public_sites error for {name}: {e}')
                    continue

    async def is_blacklisted(self, ip):
        """异步多DNSBL黑名单检测。轮询多个DNSBL区（zen.spamhaus.org, barracuda, spamcop）以降低漏报和网络抖动。"""
        if not ENABLE_DNSBL:
            return False
        try:
            reversed_ip = ".".join(reversed(ip.split(".")))
            for zone in DNSBL_ZONES:
                query = f"{reversed_ip}.{zone}"
                try:
                    await asyncio.to_thread(dns.resolver.resolve, query, "A", lifetime=5.0)
                    # 任一区返回成功（找到记录）即表示被黑名单 
                    self.logger.debug("IP %s blacklisted in %s", ip, zone)
                    return True
                except Exception:
                    # 该区查询失败，继续尝试下一区
                    continue
            return False
        except Exception as e:
            self.logger.debug("dnsbl check failed for %s: %s", ip, e)
            return False

    def check_local_db(self, ip):
        """本地数据库快速初筛"""
        if not self.reader: return True # 没库默认放行
        try:
            response = self.reader.asn(ip)
            org = response.autonomous_system_organization.lower()
            # 检查 ASN 是否包含机房关键词
            for kw in BAD_ASN_KEYWORDS:
                if kw in org: return False
            return True
        except Exception as e:
            # 在本地库解析失败时允许通过，但记录调试信息
            if hasattr(self, 'logger'):
                self.logger.debug("check_local_db failed for %s: %s", ip, e)
            return True

    def score_candidate(self, data: dict, ip: str, port: int):
        """对候选节点按多维度打分并返回 (score, reasons:list)。
        规则（可调整）:
        - hosting True -> 强制拒绝
        - DNSBL 在 strict 模式下强制拒绝；在 balanced 下扣分
        - ASN 包含 BAD_ASN_KEYWORDS: strict 扣 3，balanced 扣 1，lenient 扣 0
        - mobile True 加 COUNTRY_MOBILE_REWARD 分（住宅/手机优先）
        - 国家在 TARGET_COUNTRIES 加 COUNTRY_MOBILE_REWARD 分
        - 常见代理端口(1080,1081,10808,9050,3128,8080) + 随机高端口(5678,12345,22222等) 加 PORT_REWARD 分
        """
        score = 0.0
        reasons = []

        # hosting -> 强制拒绝
        if data.get('hosting'):
            return -999.0, ['hosting_detected']

        # mobile / country 使用可配置奖励
        if data.get('mobile'):
            score += COUNTRY_MOBILE_REWARD
            reasons.append('mobile')

        # country
        cc = data.get('countryCode')
        if TARGET_COUNTRIES and cc in TARGET_COUNTRIES:
            score += COUNTRY_MOBILE_REWARD
            reasons.append(f'country_{cc}')

        # 端口奖励：包括常见代理端口 + 2025年常见的随机高端口
        # 传统代理端口
        common_proxy_ports = {1080, 1081, 10808, 9050, 3128, 8080}
        # 2025年真实住宅/手机SOCKS5常见的随机高端口
        residential_high_ports = {
            5678, 12345, 22222, 33333, 44444, 55555, 
            60080, 9999, 8888, 7777, 6666, 11111,
            2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000,
            10000, 15000, 20000, 25000, 30000, 40000, 50000
        }
        if port in common_proxy_ports or port in residential_high_ports:
            score += PORT_REWARD
            reasons.append(f'port_{port}')

        # ASN penalty
        asn_penalty = 0
        try:
            if self.reader:
                resp = self.reader.asn(ip)
                org = (resp.autonomous_system_organization or '').lower()
                for kw in BAD_ASN_KEYWORDS:
                    if kw in org:
                        if FILTER_MODE == 'strict':
                            asn_penalty = 3
                        elif FILTER_MODE == 'balanced':
                            asn_penalty = 0.5
                        else:
                            asn_penalty = 0
                        reasons.append('bad_asn')
                        break
        except Exception:
            pass
        score -= asn_penalty

        return score, reasons

    async def fetch_ip_info(self, ip, connector):
        """轮询多个IP信息提供商，顺序优化以避免限流：ip-api > ipinfo > ipapi.co
        每个请求加随机延迟(0.2-0.8s) 以规避并发限流"""
        import random
        
        providers = [
            ('ip-api', 'http://ip-api.com/json/{ip}?fields=status,countryCode,isp,mobile,hosting,query', 0.5),
            ('ipinfo', 'https://ipinfo.io/{ip}/json', 0.5),
            ('ipapi', 'https://ipapi.co/{ip}/json/', 0.8),  # 放在最后以规避其限流
        ]
        
        for prov_name, url_tpl, base_delay in providers:
            # 随机延迟 + base_delay，避免并发一起请求同一提供商
            delay = base_delay + random.uniform(0.2, 0.8)
            await asyncio.sleep(delay)
            
            url = url_tpl.format(ip=ip)
            try:
                async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.get(url, ssl=False) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                        
                        if prov_name == 'ip-api':
                            if data.get('status') == 'success':
                                return data
                        elif prov_name == 'ipinfo':
                            return {
                                'status': 'success',
                                'countryCode': data.get('country'),
                                'isp': data.get('org') or data.get('hostname'),
                                'mobile': False,
                                'hosting': False,
                                'query': ip,
                            }
                        elif prov_name == 'ipapi':
                            return {
                                'status': 'success',
                                'countryCode': data.get('country_code'),
                                'isp': data.get('org') or data.get('asn'),
                                'mobile': data.get('is_vpn', False) or data.get('is_mobile', False),
                                'hosting': data.get('is_datacenter', False),
                                'query': ip,
                            }
            except Exception:
                continue
        return None

    async def test_proxy_connectivity(self, proxy_url, connector, timeout=8):
        """通过代理对少数可靠的轻量 URL 发起请求，验证代理是否能访问外网。
        返回 True 表示至少有一个请求成功（status 200/204/301/302），否则 False。
        """
        test_urls = [
            "http://clients3.google.com/generate_204",
            "https://www.cloudflare.com/cdn-cgi/trace",
            "https://httpbin.org/get",
        ]
        try:
            # 使用传入的 ProxyConnector 去请求外部 URL
            async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                for url in test_urls:
                    try:
                        async with session.get(url, ssl=False) as resp:
                            status = resp.status
                            if status in (200, 204, 301, 302):
                                return True
                    except Exception:
                        # 单个 URL 失败则尝试下一个
                        continue
        except Exception:
            return False
        return False

    async def verify_proxy(self, ip_port):
        ip = ip_port.split(":")[0]
        try:
            port = int(ip_port.split(":")[1])
        except Exception:
            port = 0

        # --- 第一道防线：本地数据库 (毫秒级) ---
        if USE_LOCAL_DB and not self.check_local_db(ip):
            return None

        # --- 第三道防线：真机实测 (最慢，最后做) ---
        proxy_url = f"socks5://{ip_port}"
        connector = ProxyConnector.from_url(proxy_url, rdns=True)
        
        try:
            # 真实外网连通性测试（可配置强度，默认禁用以提高通过率）
            connectivity_ok = True  # 默认跳过，除非用户显式启用
            if getattr(self, 'check_connectivity', False):  # 默认 False（禁用）
                ok = await self.test_proxy_connectivity(proxy_url, connector, timeout=getattr(self, 'connectivity_timeout', 8))
                if not ok:
                    # strict 模式直接拒绝，balanced 和 lenient 模式扣分
                    if FILTER_MODE == 'strict':
                        return None
                    # balanced/lenient 继续，但稍后会扣分
                    connectivity_ok = False

            data = await self.fetch_ip_info(ip, connector)
            if not data:
                return None

            # hosting 强拒绝
            if data.get('hosting'):
                self.logger.info('%s rejected: hosting detected', ip_port)
                return None

            # DNSBL 检查（多区轮询）
            is_black = await self.is_blacklisted(ip)
            if is_black and FILTER_MODE == 'strict':
                print(("⚠️ " if EMOJI_ENABLED else "") + f"[剔除] 黑名单IP | {ip}")
                return None

            # 打分评估
            score, reasons = self.score_candidate(data, ip, port)

            # DNSBL 在 balanced 模式下扣分
            if is_black and FILTER_MODE == 'balanced':
                score -= 1
                reasons.append('dnsbl')

            # 连通性测试在 balanced/lenient 模式下扣分
            if not connectivity_ok and FILTER_MODE in ('balanced', 'lenient'):
                score -= 0.5
                reasons.append('connectivity_weak')

            # 根据 EMOJI_ENABLED 决定是否使用 emoji
            if EMOJI_ENABLED:
                tag = "📱 手机" if data.get("mobile") else "🏠 家宽"
            else:
                tag = "mobile" if data.get("mobile") else "residential"
            cc = data.get('countryCode')

            # 决策
            try:
                threshold = GLOBAL_SCORE_THRESHOLD
            except NameError:
                threshold = 1.0

            self.logger.info('candidate %s score=%.2f reasons=%s', ip_port, score, reasons)

            if score >= threshold:
                reasons_str = '|'.join(reasons)
                output_line = f"{proxy_url} # {cc}_{tag} | score={score} | reasons={reasons_str}"
                print(("✅ " if EMOJI_ENABLED else "") + output_line)
                return output_line
            else:
                self.logger.info('%s rejected by score %.2f < %.2f', ip_port, score, threshold)
                return None
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.debug("verify_proxy failed for %s: %s", ip_port, e)
            return None

    async def run(self):
        await self.fetch_sources()
        
        sem = asyncio.Semaphore(MAX_CONCURRENCY)
        async def bounded(p):
            async with sem:
                res = await self.verify_proxy(p)
                if res: self.clean_proxies.append(res)

        await asyncio.gather(*[bounded(p) for p in self.raw_proxies])

        if self.clean_proxies:
            with open("Industrial_Socks5.txt", "w", encoding='utf-8') as f:
                f.write("\n".join(self.clean_proxies))
            print(("\n🎉 " if EMOJI_ENABLED else "\n") + f"清洗完成！获得 {len(self.clean_proxies)} 个工业级纯净节点")
        else:
            print(("\n❌ " if EMOJI_ENABLED else "\n") + f"未找到符合条件的节点")

if __name__ == "__main__":
    import platform
    if platform.system() == "Windows":
        # Windows 上需要使用 SelectorEventLoop 来支持 aiodns
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # 默认打印 INFO 级别日志，便于查看 fetch_sources 的状态
    import logging as _logging
    _logging.basicConfig(level=_logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    # 支持命令行选项：--lenient（宽松模式，禁用 DNSBL/本地 ASN 过滤），
    # 以及 --sources-file <path> 从本地文件加载额外的源（每行一个 URL）
    parser = argparse.ArgumentParser(description='Industrial Socks5 Cleaner')
    parser.add_argument('--lenient', action='store_true', help='Disable DNSBL and local ASN filtering (less strict)')
    parser.add_argument('--filter-mode', choices=['strict','balanced','lenient'], default='strict', help='Filter mode: strict (default), balanced (less strict), lenient (disable several checks)')
    parser.add_argument('--sources-file', type=str, help='Path to a file containing extra sources (one per line)')
    # FOFA 参数（可选）：在本地提供 email/key 后会调用 FOFA API，并把结果追加到候选列表
    parser.add_argument('--fofa-email', type=str, help='FOFA account email for API access')
    parser.add_argument('--fofa-key', type=str, help='FOFA API key')
    parser.add_argument('--fofa-query', type=str, help='FOFA search query (eg. "title=\"Clash\" && protocol==\"socks5\"")')
    parser.add_argument('--fofa-size', type=int, default=100, help='FOFA page size (max per request)')
    parser.add_argument('--fofa-pages', type=int, default=1, help='Maximum FOFA pages to fetch')
    parser.add_argument('--fofa-force', action='store_true', help='Force refresh FOFA cache (ignore local cache)')
    parser.add_argument('--fetch-proxy', type=str, default="http://127.0.0.1:62809", help='Optional proxy URL to use for fetching sources')
    parser.add_argument('--port-reward', type=float, help='Reward for common proxy ports (overrides default)')
    parser.add_argument('--country-mobile-reward', type=float, help='Reward for country/mobile match (overrides default)')
    parser.add_argument('--score-threshold', type=float, help='Global score threshold to accept a candidate (overrides default per filter-mode)')
    parser.add_argument('--emoji', action='store_true', help='Force-enable emoji output (overrides platform default)')
    parser.add_argument('--no-emoji', action='store_true', help='Disable emoji output')
    parser.add_argument('--concurrency', type=int, help='Max concurrent proxy tests (default 100)')
    parser.add_argument('--connectivity', action='store_true', help='Enable heavyweight connectivity tests (HTTP via proxy) - disabled by default')
    parser.add_argument('--connectivity-timeout', type=int, default=8, help='Timeout seconds for connectivity test requests (default 8)')
    parser.add_argument('--quick', action='store_true', help='Quick mode: use first 3 sources only, skip public sites, lower concurrency')
    parser.add_argument('--no-public', action='store_true', help='Skip public proxy site scraping')
    args = parser.parse_args()

    # CLI override for emoji display: explicit flags win
    if getattr(args, 'emoji', False):
        EMOJI_ENABLED = True
    if getattr(args, 'no_emoji', False):
        EMOJI_ENABLED = False

    # 并发控制
    if args.concurrency:
        MAX_CONCURRENCY = args.concurrency
        _logging.info('Concurrency set to %d', MAX_CONCURRENCY)
    
    # --quick 模式：快速测试，仅用前 3 个源，降低并发，跳过公开站点
    if args.quick:
        SOURCES[:] = SOURCES[:3]
        MAX_CONCURRENCY = min(MAX_CONCURRENCY, 20)
        _logging.info('Quick mode: using first 3 sources, concurrency=%d', MAX_CONCURRENCY)
        args.no_public = True

    # 如果提供了本地 sources 文件，加载并追加到 SOURCES
    if args.sources_file:
        load_sources_from_file(os.path.abspath(args.sources_file))

    # 多源采集 orchestrator：先抓公开网站，再 FOFA，最后执行常规检测
    async def _orchestrator():
        cleaner = IndustrialCleaner()

        # 如果用户提供了 fetch-proxy，在 cleaner 上设置对应的 connector
        if args.fetch_proxy:
            try:
                cleaner.fetch_connector = ProxyConnector.from_url(args.fetch_proxy)
                _logging.info('Configured fetch proxy: %s', args.fetch_proxy)
            except Exception as e:
                _logging.warning('Failed to create fetch connector from %s: %s', args.fetch_proxy, e)

        # 连通性检测控制：默认禁用（太严格），用户可通过 --connectivity 显式启用
        cleaner.check_connectivity = getattr(args, 'connectivity', False)  # 默认 False
        cleaner.connectivity_timeout = getattr(args, 'connectivity_timeout', 8)

        # 第一步：从公开网站抓取（无需凭证）
        if not args.no_public:
            _logging.info('Fetching from public proxy sites (no auth required)...')
            await cleaner.fetch_from_public_sites()
        else:
            _logging.info('Skipping public proxy sites (--no-public or --quick mode)')

        # 第二步：如果指定了 FOFA 参数，优先尝试使用本地缓存，除非用户强制刷新
        if args.fofa_key and args.fofa_email and args.fofa_query:
            _logging.info('FOFA fetch requested (using local cache unless --fofa-force provided)')
            try:
                if os.path.exists(FOFA_CACHE_FILE) and not args.fofa_force:
                    # 从本地 cache 加载（按行），并加入候选集合
                    with open(FOFA_CACHE_FILE, 'r', encoding='utf-8') as cf:
                        cached = [l.strip() for l in cf if l.strip()]
                    cleaner.raw_proxies.update(cached)
                    _logging.info('Loaded %s entries from FOFA cache (%s)', len(cached), FOFA_CACHE_FILE)
                else:
                    _logging.info('Fetching from FOFA API (this may consume your FOFA quota)')
                    found = await cleaner.fetch_from_fofa(args.fofa_email, args.fofa_key, args.fofa_query, size=args.fofa_size, max_pages=args.fofa_pages)
                    # 将新找到的结果写入本地缓存以便未来使用（覆盖）
                    try:
                        if found:
                            with open(FOFA_CACHE_FILE, 'w', encoding='utf-8') as cf:
                                cf.write('\n'.join(sorted(found)))
                            _logging.info('Wrote %s FOFA results to cache %s', len(found), FOFA_CACHE_FILE)
                        else:
                            _logging.info('FOFA returned no new results; cache not updated')
                    except Exception as e:
                        _logging.warning('Failed to write FOFA cache: %s', e)
            except Exception as e:
                _logging.warning('FOFA cache/fetch handling failed: %s', e)
        
        # 第三步：继续常规采集与检测流程
        await cleaner.run()

    # 宽松模式：禁用黑名单与本地 ASN 过滤，避免过度剔除
    # 支持三种过滤模式：strict (默认) / balanced / lenient
    FILTER_MODE = args.filter_mode
    if args.filter_mode == 'lenient' or args.lenient:
        ENABLE_DNSBL = False
        USE_LOCAL_DB = False
        BAD_ASN_KEYWORDS = []
        _logging.info('Lenient mode enabled: DNSBL and local ASN checks disabled')

    # 全局评分阈值：如果用户提供则覆盖默认；否则按 filter-mode 选择默认值
    if args.score_threshold is not None:
        GLOBAL_SCORE_THRESHOLD = float(args.score_threshold)
    else:
        if FILTER_MODE == 'strict':
            GLOBAL_SCORE_THRESHOLD = 0.0  # 严格模式：接受所有通过 IP 验证的节点（基线）
        elif FILTER_MODE == 'balanced':
            GLOBAL_SCORE_THRESHOLD = 0.0  # 平衡模式：接受所有通过 IP 验证的节点（包括基础分 0.5 减扣后）
        else:
            GLOBAL_SCORE_THRESHOLD = -999.0  # 宽松模式：几乎接受所有
    _logging.info('Global score threshold set to %.2f (mode=%s)', GLOBAL_SCORE_THRESHOLD, FILTER_MODE)

    # 奖励参数：允许用户通过命令行覆盖默认奖励
    if args.port_reward is not None:
        PORT_REWARD = float(args.port_reward)
    else:
        PORT_REWARD = 1.0  # 2025年优化默认值

    if args.country_mobile_reward is not None:
        COUNTRY_MOBILE_REWARD = float(args.country_mobile_reward)
    else:
        COUNTRY_MOBILE_REWARD = 1.8  # 2025年优化默认值

    _logging.info('PORT_REWARD=%.2f COUNTRY_MOBILE_REWARD=%.2f', PORT_REWARD, COUNTRY_MOBILE_REWARD)

    asyncio.run(_orchestrator())