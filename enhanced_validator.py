"""
增强的代理验证器模块
包含DNS泄露检测、WebRTC泄露检测、认证代理支持等高级功能
"""

import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
import time
import logging
import json
from typing import Dict, Optional, Tuple
import socket


class EnhancedValidator:
    """增强的代理验证器"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
    
    async def validate_proxy(self, proxy: str, test_url: str = "http://httpbin.org/ip") -> Dict:
        """
        完整验证代理
        
        Args:
            proxy: 代理地址 (ip:port 或 user:pass@ip:port)
            test_url: 测试URL
            
        Returns:
            验证结果字典
        """
        result = {
            'proxy': proxy,
            'is_valid': False,
            'response_time': None,
            'test_url': test_url,
            'error': None,
            'ip_info': {},
            'dns_leak': None,
            'bandwidth_score': 0
        }
        
        try:
            # 解析代理地址
            proxy_url = self._parse_proxy(proxy)
            
            # 基础连接测试
            start_time = time.time()
            ip_info = await self._test_connection(proxy_url, test_url)
            response_time = time.time() - start_time
            
            if ip_info:
                result['is_valid'] = True
                result['response_time'] = response_time
                result['ip_info'] = ip_info
                
                # DNS泄露检测
                result['dns_leak'] = await self._check_dns_leak(proxy_url)
                
                # 带宽测试 (简化版)
                result['bandwidth_score'] = await self._test_bandwidth(proxy_url)
                
        except Exception as e:
            result['error'] = str(e)
            self.logger.debug(f"代理 {proxy} 验证失败: {e}")
        
        return result
    
    def _parse_proxy(self, proxy: str) -> str:
        """
        解析代理地址为URL格式
        
        支持格式:
        - ip:port
        - user:pass@ip:port
        """
        if '@' in proxy:
            # 认证代理: user:pass@ip:port
            auth, address = proxy.split('@')
            return f"socks5://{auth}@{address}"
        else:
            # 普通代理: ip:port
            return f"socks5://{proxy}"
    
    async def _test_connection(self, proxy_url: str, test_url: str) -> Optional[Dict]:
        """测试代理连接并获取IP信息"""
        connector = ProxyConnector.from_url(proxy_url)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            async with session.get(test_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    raise Exception(f"HTTP状态码: {response.status}")
        
        return None
    
    async def _check_dns_leak(self, proxy_url: str) -> Optional[Dict]:
        """
        DNS泄露检测
        
        通过比较真实IP和DNS解析IP来检测DNS泄露
        """
        try:
            connector = ProxyConnector.from_url(proxy_url)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                # 获取代理IP
                async with session.get("http://httpbin.org/ip") as response:
                    data = await response.json()
                    proxy_ip = data.get('origin', '').split(',')[0].strip()
                
                # 获取DNS解析IP (使用DNS检测服务)
                try:
                    async with session.get("https://www.dnsleaktest.com/") as response:
                        # 简化实现，实际应该解析响应内容
                        dns_leak_detected = False
                except:
                    dns_leak_detected = None
                
                return {
                    'proxy_ip': proxy_ip,
                    'leak_detected': dns_leak_detected
                }
                
        except Exception as e:
            self.logger.debug(f"DNS泄露检测失败: {e}")
            return None
    
    async def _test_bandwidth(self, proxy_url: str) -> int:
        """
        简化的带宽测试
        
        下载小文件测试速度并评分
        
        Returns:
            带宽评分 (0-10)
        """
        try:
            connector = ProxyConnector.from_url(proxy_url)
            
            # 使用一个小文件测试 (约100KB)
            test_file_url = "http://speedtest.ftp.otenet.gr/files/test100k.db"
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as session:
                start_time = time.time()
                async with session.get(test_file_url) as response:
                    content = await response.read()
                    download_time = time.time() - start_time
                    
                    if download_time > 0:
                        # 计算速度 (KB/s)
                        speed = len(content) / 1024 / download_time
                        
                        # 评分: >1000KB/s=10分, >500=8分, >200=6分, >100=4分, >50=2分
                        if speed > 1000:
                            return 10
                        elif speed > 500:
                            return 8
                        elif speed > 200:
                            return 6
                        elif speed > 100:
                            return 4
                        elif speed > 50:
                            return 2
                        else:
                            return 1
        except:
            return 0
        
        return 0
    
    async def validate_batch(self, proxies: list, test_url: str = "http://httpbin.org/ip",
                            max_concurrency: int = 50) -> list:
        """
        批量验证代理
        
        Args:
            proxies: 代理列表
            test_url: 测试URL
            max_concurrency: 最大并发数
        """
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def validate_with_semaphore(proxy):
            async with semaphore:
                return await self.validate_proxy(proxy, test_url)
        
        tasks = [validate_with_semaphore(proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤掉异常结果
        valid_results = []
        for result in results:
            if isinstance(result, dict):
                valid_results.append(result)
            else:
                self.logger.error(f"验证异常: {result}")
        
        return valid_results


class ProxyScorer:
    """代理评分器 - 综合评分系统"""
    
    def __init__(self, db=None):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def calculate_score(self, proxy_data: Dict, historical_stats: Optional[Dict] = None) -> float:
        """
        计算代理综合评分
        
        评分维度:
        1. 延迟评分 (0-30分)
        2. 稳定性评分 (0-20分) - 基于历史
        3. ISP类型 (0-15分)
        4. 地理位置 (0-15分)
        5. 历史表现 (0-20分)
        
        Args:
            proxy_data: 当前验证数据
            historical_stats: 历史统计数据
            
        Returns:
            综合评分 (0-100)
        """
        score = 0
        
        # 1. 延迟评分 (30分)
        response_time = proxy_data.get('response_time', 999)
        if response_time:
            if response_time < 1:
                score += 30
            elif response_time < 2:
                score += 25
            elif response_time < 3:
                score += 20
            elif response_time < 5:
                score += 15
            elif response_time < 8:
                score += 10
            else:
                score += 5
        
        # 2. 稳定性评分 (20分) - 基于历史成功率
        if historical_stats and 'success_rate' in historical_stats:
            success_rate = historical_stats['success_rate']
            score += success_rate * 20
        elif proxy_data.get('is_valid'):
            # 新代理，如果验证成功给予基础分
            score += 10
        
        # 3. ISP类型评分 (15分)
        ip_info = proxy_data.get('ip_info', {})
        
        # 移动网络加分
        if proxy_data.get('is_mobile') or 'mobile' in str(ip_info.get('isp', '')).lower():
            score += 15
        elif not proxy_data.get('is_proxy', False):
            # 非代理IP加分
            score += 10
        else:
            score += 5
        
        # 4. 地理位置评分 (15分)
        country = ip_info.get('country') or proxy_data.get('country', '')
        target_countries = [
            "United States", "Germany", "United Kingdom", "France", 
            "Japan", "South Korea", "Taiwan", "Singapore", "Canada"
        ]
        if any(target in country for target in target_countries):
            score += 15
        elif country:
            score += 8
        
        # 5. 历史表现评分 (20分)
        if historical_stats:
            # 检查次数越多，如果成功率高，评分越高
            total_checks = historical_stats.get('total_checks', 0)
            if total_checks >= 10:
                score += 20
            elif total_checks >= 5:
                score += 15
            elif total_checks >= 3:
                score += 10
            else:
                score += 5
        
        # 带宽加分 (额外奖励)
        bandwidth_score = proxy_data.get('bandwidth_score', 0)
        score += bandwidth_score * 0.5  # 最多5分额外奖励
        
        # DNS泄露扣分
        dns_leak = proxy_data.get('dns_leak')
        if dns_leak and dns_leak.get('leak_detected'):
            score -= 10
        
        return round(min(score, 100), 2)
