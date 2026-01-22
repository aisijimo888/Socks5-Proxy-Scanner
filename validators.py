"""
代理验证器模块
"""

import asyncio
import aiohttp
import time
import logging
from typing import List, Dict
from aiohttp_socks import ProxyConnector
from tqdm.asyncio import tqdm # 引入tqdm


class ProxyValidator:
    """代理验证器"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.semaphore = asyncio.Semaphore(config.max_concurrency)
        
    async def validate_proxies(self, proxies: List[str]) -> List[Dict]:
        """验证代理列表"""
        if not proxies:
            return []
        
        self.logger.info(f"开始验证 {len(proxies)} 个代理")
        
        tasks = [self._validate_single_proxy(proxy) for proxy in proxies]
        all_results = []  # 改为保存所有结果

        # 使用 asyncio.as_completed 和 tqdm 手动处理进度
        with tqdm(total=len(proxies), desc="验证代理", unit="个") as pbar:
            for future in asyncio.as_completed(tasks):
                try:
                    result = await future
                    # 保存所有结果（成功和失败的）
                    all_results.append(result)
                except Exception as e:
                    # 代理验证过程中可能会抛出各种异常 (e.g., connection errors)
                    # 我们在这里捕获它们，记录日志，然后继续处理下一个
                    self.logger.debug(f"代理验证失败: {e}")
                finally:
                    pbar.update(1)
        
        # 统计有效代理
        valid_proxies = [r for r in all_results if r and r.get('is_valid')]
        self.logger.info(f"验证完成，{len(valid_proxies)}/{len(proxies)} 个代理有效")
        
        # 应用国家白名单过滤
        if self.config.target_countries:
            filtered_proxies = self._filter_by_country(valid_proxies)
            self.logger.info(f"国家白名单过滤后，{len(filtered_proxies)}/{len(valid_proxies)} 个代理保留")
            # 返回所有结果：过滤后的成功 + 所有失败
            failed_results = [r for r in all_results if r and not r.get('is_valid')]
            return filtered_proxies + failed_results
        
        return all_results  # 返回所有结果（包括None的会被过滤）
    
    def _filter_by_country(self, proxies: List[Dict]) -> List[Dict]:
        """根据国家白名单过滤代理"""
        filtered = []
        target_countries = [country.lower() for country in self.config.target_countries]
        
        for proxy in proxies:
            country = proxy.get('country', 'Unknown').lower()
            city = proxy.get('city', 'Unknown')
            
            # 检查国家是否在白名单中
            if country in target_countries:
                filtered.append(proxy)
            else:
                # 检查国家别名
                country_found = False
                for alias, full_name in getattr(self.config, 'country_aliases', {}).items():
                    if country == full_name.lower() and full_name.lower() in target_countries:
                        filtered.append(proxy)
                        country_found = True
                        break
                
                if not country_found:
                    self.logger.debug(f"代理 {proxy['proxy']} 被过滤（国家: {country}, 城市: {city}）")
        
        return filtered
    
    async def _validate_single_proxy(self, proxy: str) -> Dict:
        """验证单个代理"""
        async with self.semaphore:
            try:
                ip, port = proxy.split(':')
                port = int(port)
                
                start_time = time.time()
                
                connector = ProxyConnector.from_url(f"socks5://{proxy}")
                
                async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as session:
                    
                    test_url = self.config.test_urls[0]
                    async with session.get(test_url) as response:
                        if response.status == 200:
                            response_time = time.time() - start_time
                            geo_info = await self._get_geo_info(session)
                            
                            # 创建完整的验证结果
                            result = {
                                'proxy': proxy,
                                'ip': ip,
                                'port': port,
                                'is_valid': True,  # ← 添加
                                'response_time': response_time,
                                'test_url': test_url,  # ← 添加
                                'country': geo_info.get('country', 'Unknown'),
                                'country_code': self._get_country_code(geo_info.get('country', 'Unknown')),  # ← 添加
                                'city': geo_info.get('city', 'Unknown'),
                                'isp': geo_info.get('isp', 'Unknown'),  # ← 添加
                                'is_mobile': geo_info.get('mobile', False),  # ← 添加
                                'is_proxy': geo_info.get('proxy', False),  # ← 添加
                                'score': self._calculate_score(response_time, geo_info)
                            }
                            
                            return result
                        else:
                            # 返回失败结果而不是 None
                            return {
                                'proxy': proxy,
                                'ip': ip,
                                'port': port,
                                'is_valid': False,
                                'error': f'HTTP {response.status}'
                            }
                            
            except Exception as e:
                self.logger.debug(f"代理 {proxy} 验证时出错: {e}")
                # 返回失败结果
                try:
                    ip, port = proxy.split(':')
                    return {
                        'proxy': proxy,
                        'ip': ip,
                        'port': int(port),
                        'is_valid': False,
                        'error': str(e)
                    }
                except:
                    return None  # 如果连解析都失败，返回None
    
    async def _get_geo_info(self, session: aiohttp.ClientSession) -> Dict:
        """获取地理位置信息"""
        try:
            async with session.get("http://ip-api.com/json/") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'country': data.get('country', 'Unknown'),
                        'city': data.get('city', 'Unknown'),
                        'isp': data.get('isp', 'Unknown'),
                        'mobile': data.get('mobile', False),
                        'proxy': data.get('proxy', False)
                    }
        except Exception as e:
            self.logger.warning(f"获取地理位置失败: {e}")
            raise  # 重新抛出异常，让上层捕获
    
    def _calculate_score(self, response_time: float, geo_info: Dict) -> float:
        """计算代理评分"""
        score = 10.0
        
        if response_time < 1.0:
            score += 5.0
        elif response_time < 3.0:
            score += 3.0
        elif response_time < 5.0:
            score += 1.0
        else:
            score -= 2.0
        
        if geo_info.get('mobile'):
            score += 2.0
        
        if geo_info.get('proxy'):
            score -= 3.0
        
        return max(0.0, score)
    
    def _get_country_code(self, country: str) -> str:
        """根据国家名获取国家代码"""
        country_codes = {
            'United States': 'US',
            'Japan': 'JP',
            'Germany': 'DE',
            'Singapore': 'SG',
            'Netherlands': 'NL',
            'United Kingdom': 'GB',
            'Canada': 'CA',
            'France': 'FR',
            'South Korea': 'KR',
            'Taiwan': 'TW',
            'Switzerland': 'CH',
            'Sweden': 'SE',
            'Australia': 'AU',
            'Unknown': 'UN'
        }
        return country_codes.get(country, country[:2].upper() if len(country) >= 2 else 'UN')
