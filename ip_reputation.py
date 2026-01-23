"""
IP 信誉和黑名单检测模块
检测代理IP是否被 Cloudflare、Google 等服务拉黑
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from timezone_utils import now_utc


class IPReputationChecker:
    """IP信誉检测器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache = {}  # IP信誉缓存
        self.cache_ttl = timedelta(hours=24)  # 缓存24小时
    
    async def check_reputation(self, proxy_address: str, session: aiohttp.ClientSession) -> Dict:
        """
        检查代理的信誉
        
        Args:
            proxy_address: 代理地址 (IP:端口)
            session: aiohttp会话（已通过代理配置）
        
        Returns:
            信誉信息字典
        """
        ip = proxy_address.split(':')[0]
        
        # 检查缓存
        if ip in self.cache:
            cached_data, cached_time = self.cache[ip]
            if now_utc() - cached_time < self.cache_ttl:
                return cached_data
        
        reputation = {
            'ip': ip,
            'cloudflare_blocked': False,
            'google_blocked': False,
            'is_vpn': False,
            'is_proxy': False,
            'is_tor': False,
            'is_datacenter': False,
            'threat_score': 0,  # 0-100，100最差
            'check_time': now_utc().isoformat()
        }
        
        # 并发检查多个服务
        tasks = [
            self._check_cloudflare(session, reputation),
            self._check_google(session, reputation),
            self._check_ipqualityscore(ip, reputation),
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # 计算综合威胁分数
        reputation['threat_score'] = self._calculate_threat_score(reputation)
        
        # 缓存结果
        self.cache[ip] = (reputation, now_utc())
        
        return reputation
    
    async def _check_cloudflare(self, session: aiohttp.ClientSession, reputation: Dict):
        """检查是否被Cloudflare拉黑"""
        try:
            # 访问一个使用Cloudflare保护的网站
            test_url = "https://www.cloudflare.com/cdn-cgi/trace"
            
            async with session.get(test_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 403:
                    reputation['cloudflare_blocked'] = True
                elif response.status == 200:
                    text = await response.text()
                    # 检查是否有challenge页面
                    if 'cf-chl-bypass' in text or 'challenge-platform' in text:
                        reputation['cloudflare_blocked'] = True
        except Exception as e:
            self.logger.debug(f"Cloudflare检测失败: {e}")
    
    async def _check_google(self, session: aiohttp.ClientSession, reputation: Dict):
        """检查是否被Google拉黑"""
        try:
            # 访问Google
            test_url = "https://www.google.com/search?q=test"
            
            async with session.get(test_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 429:  # Too Many Requests
                    reputation['google_blocked'] = True
                elif response.status == 200:
                    text = await response.text()
                    # 检查是否有CAPTCHA
                    if 'recaptcha' in text.lower() or 'unusual traffic' in text.lower():
                        reputation['google_blocked'] = True
        except Exception as e:
            self.logger.debug(f"Google检测失败: {e}")
    
    async def _check_ipqualityscore(self, ip: str, reputation: Dict):
        """
        通过IP-API.com检查IP类型
        (免费版，无需API key)
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://ip-api.com/json/{ip}?fields=proxy,hosting,mobile"
                
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        reputation['is_proxy'] = data.get('proxy', False)
                        reputation['is_datacenter'] = data.get('hosting', False)
                        reputation['is_mobile'] = data.get('mobile', False)
        except Exception as e:
            self.logger.debug(f"IP类型检测失败: {e}")
    
    def _calculate_threat_score(self, reputation: Dict) -> int:
        """
        计算综合威胁分数
        0-100，分数越高越可疑
        """
        score = 0
        
        # Cloudflare拉黑 +50分
        if reputation['cloudflare_blocked']:
            score += 50
        
        # Google拉黑 +40分
        if reputation['google_blocked']:
            score += 40
        
        # 已知代理 +20分
        if reputation['is_proxy']:
            score += 20
        
        # Tor节点 +30分
        if reputation['is_tor']:
            score += 30
        
        # 数据中心IP +10分
        if reputation['is_datacenter']:
            score += 10
        
        return min(score, 100)
    
    def is_blacklisted(self, reputation: Dict) -> bool:
        """
        判断是否应该拉黑
        
        威胁分数 >= 70 建议拉黑
        """
        return reputation['threat_score'] >= 70
    
    def get_risk_level(self, reputation: Dict) -> str:
        """获取风险等级"""
        score = reputation['threat_score']
        
        if score >= 80:
            return "高风险"
        elif score >= 50:
            return "中风险"
        elif score >= 20:
            return "低风险"
        else:
            return "正常"


# 示例使用
async def example_usage():
    """示例：如何使用IP信誉检测"""
    checker = IPReputationChecker()
    
    # 创建通过代理的会话
    from aiohttp_socks import ProxyConnector
    
    proxy = "1.2.3.4:1080"
    connector = ProxyConnector.from_url(f"socks5://{proxy}")
    
    async with aiohttp.ClientSession(connector=connector) as session:
        reputation = await checker.check_reputation(proxy, session)
        
        print(f"IP: {reputation['ip']}")
        print(f"威胁分数: {reputation['threat_score']}")
        print(f"风险等级: {checker.get_risk_level(reputation)}")
        print(f"Cloudflare拉黑: {reputation['cloudflare_blocked']}")
        print(f"Google拉黑: {reputation['google_blocked']}")
        print(f"建议拉黑: {checker.is_blacklisted(reputation)}")


if __name__ == "__main__":
    asyncio.run(example_usage())
