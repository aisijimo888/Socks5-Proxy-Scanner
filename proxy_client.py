"""
代理客户端SDK
供其他项目调用的Python SDK库
"""

import os
import sys
import requests
import random
import socket
from typing import List, Dict, Optional

# 尝试加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv未安装，使用默认值


def get_local_ip():
    """
    自动获取本机IP地址
    
    Returns:
        本机IP地址
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


class ProxyClient:
    """
    代理客户端SDK
    
    使用示例:
        # 方式1: 使用默认配置 (从.env读取)
        client = ProxyClient()
        
        # 方式2: 指定API地址
        client = ProxyClient('http://192.168.1.100:8080')
        
        # 方式3: 自动检测本机IP
        client = ProxyClient.from_local_ip()
        
        proxy = client.get_random()
        print(proxy)  # socks5://1.2.3.4:1080
    """
    
    def __init__(self, api_url: str = None, timeout: int = 10):
        """
        初始化客户端
        
        Args:
            api_url: API服务器地址 (不提供则从环境变量读取)
            timeout: 请求超时时间(秒)
        
        环境变量配置:
            PROXY_API_HOST: API服务器地址 (默认: localhost)
            PROXY_API_PORT: API端口 (默认: 8080)
        """
        if api_url is None:
            # 从环境变量读取配置
            host = os.getenv('PROXY_API_HOST', 'localhost')
            port = os.getenv('PROXY_API_PORT', '8080')
            api_url = f'http://{host}:{port}'
        
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self._current_proxy = None
    
    @classmethod
    def from_local_ip(cls, port: int = 8080, **kwargs):
        """
        使用本机IP地址创建客户端 (局域网访问)
        
        Args:
            port: API端口
            **kwargs: 其他参数传递给__init__
        
        Returns:
            ProxyClient实例
        
        Example:
            # 自动检测本机IP并连接
            client = ProxyClient.from_local_ip()
        """
        local_ip = get_local_ip()
        api_url = f'http://{local_ip}:{port}'
        return cls(api_url=api_url, **kwargs)
    
    def get_random(self, country: Optional[str] = None, min_score: float = 0) -> str:
        """
        获取随机代理
        
        Args:
            country: 国家代码过滤 (如 'US', 'JP')
            min_score: 最低评分
        
        Returns:
            代理地址，格式: socks5://1.2.3.4:1080
        
        Example:
            proxy = client.get_random(country='US', min_score=80)
        """
        params = {}
        if country:
            params['country'] = country
        if min_score > 0:
            params['min_score'] = min_score
        
        response = requests.get(
            f'{self.api_url}/api/proxy/random',
            params=params,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        self._current_proxy = data['address']
        return data['format']
    
    def get_best(self, limit: int = 10, country: Optional[str] = None, 
                 min_score: float = 0, detailed: bool = False) -> List:
        """
        获取最佳代理列表
        
        Args:
            limit: 返回数量
            country: 国家代码过滤
            min_score: 最低评分
            detailed: 是否返回详细信息
        
        Returns:
            代理列表
        
        Example:
            proxies = client.get_best(limit=5, country='JP')
            # ['1.2.3.4:1080', '5.6.7.8:1080', ...]
        """
        params = {
            'limit': limit,
            'format': 'detailed' if detailed else 'simple'
        }
        if country:
            params['country'] = country
        if min_score > 0:
            params['min_score'] = min_score
        
        response = requests.get(
            f'{self.api_url}/api/proxy/best',
            params=params,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        return data['proxies']
    
    def get_by_country(self, country_code: str, limit: int = 10) -> List[str]:
        """
        获取指定国家的代理
        
        Args:
            country_code: 国家代码 (如 'US', 'JP')
            limit: 返回数量
        
        Returns:
            代理地址列表
        
        Example:
            proxies = client.get_by_country('US', limit=5)
        """
        response = requests.get(
            f'{self.api_url}/api/proxy/country/{country_code}',
            params={'limit': limit},
            timeout=self.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        return data['proxies']
    
    def validate(self, proxy: str) -> bool:
        """
        验证代理是否可用
        
        Args:
            proxy: 代理地址 (格式: IP:PORT)
        
        Returns:
            是否有效
        
        Example:
            is_valid = client.validate('1.2.3.4:1080')
        """
        response = requests.get(
            f'{self.api_url}/api/proxy/validate',
            params={'proxy': proxy},
            timeout=self.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        return data['valid']
    
    def get_stats(self) -> Dict:
        """
        获取代理池统计信息
        
        Returns:
            统计数据字典
        
        Example:
            stats = client.get_stats()
            print(f"总代理数: {stats['data']['total_proxies']}")
        """
        response = requests.get(
            f'{self.api_url}/api/stats',
            timeout=self.timeout
        )
        response.raise_for_status()
        
        return response.json()
    
    def export(self, format_type: str = 'txt', limit: int = 100) -> str:
        """
        导出代理列表
        
        Args:
            format_type: 格式 (txt, json, csv)
            limit: 导出数量
        
        Returns:
            导出内容
        
        Example:
            content = client.export('txt', limit=50)
            with open('proxies.txt', 'w') as f:
                f.write(content)
        """
        response = requests.get(
            f'{self.api_url}/api/export/{format_type}',
            params={'limit': limit},
            timeout=self.timeout
        )
        response.raise_for_status()
        
        if format_type == 'json':
            return response.json()
        else:
            return response.text
    
    def with_retry(self, max_retries: int = 3, country: Optional[str] = None) -> Optional[str]:
        """
        带重试的获取代理
        
        Args:
            max_retries: 最大重试次数
            country: 国家代码过滤
        
        Returns:
            代理地址，失败返回None
        
        Example:
            proxy = client.with_retry(max_retries=5, country='US')
        """
        for attempt in range(max_retries):
            try:
                proxy = self.get_random(country=country)
                # 简单验证
                if proxy:
                    return proxy
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                continue
        
        return None
    
    def as_requests_proxies(self, proxy: Optional[str] = None) -> Dict[str, str]:
        """
        转换为requests库的proxies格式
        
        Args:
            proxy: 代理地址 (不提供则自动获取)
        
        Returns:
            requests proxies字典
        
        Example:
            import requests
            proxies = client.as_requests_proxies()
            response = requests.get('http://httpbin.org/ip', proxies=proxies)
        """
        if not proxy:
            proxy = self.get_random()
        
        return {
            'http': proxy,
            'https': proxy
        }
    
    @property
    def current_proxy(self) -> Optional[str]:
        """获取当前使用的代理"""
        return self._current_proxy
    
    def health_check(self) -> bool:
        """
        检查API服务器健康状态
        
        Returns:
            服务器是否健康
        """
        try:
            response = requests.get(
                f'{self.api_url}/health',
                timeout=5
            )
            return response.status_code == 200
        except:
            return False


# 便捷函数
def get_proxy(api_url: str = None, country: Optional[str] = None) -> str:
    """
    快速获取一个代理 (便捷函数)
    
    Args:
        api_url: API服务器地址 (不提供则使用环境变量)
        country: 国家代码
    
    Returns:
        代理地址
    
    Example:
        # 使用默认配置
        proxy = get_proxy(country='US')
        
        # 指定API地址
        proxy = get_proxy('http://192.168.1.100:8080', country='US')
    """
    client = ProxyClient(api_url)
    return client.get_random(country=country)


if __name__ == '__main__':
    # 使用示例
    print("代理客户端SDK使用示例\n")
    
    print("💡 初始化方式:")
    print("   1. 使用默认配置 (从.env读取):")
    print("      client = ProxyClient()")
    print()
    print("   2. 指定API地址:")
    print("      client = ProxyClient('http://192.168.1.100:8080')")
    print()
    print("   3. 自动检测本机IP (局域网):")
    print("      client = ProxyClient.from_local_ip()")
    print()
    
    # 初始化客户端
    client = ProxyClient()
    
    print(f"当前API地址: {client.api_url}\n")
    
    # 检查健康状态
    if client.health_check():
        print("✅ API服务器在线\n")
    else:
        print("❌ API服务器离线，请先启动: python proxy_api.py\n")
        print("💡 提示:")
        print("   1. 本机访问: python proxy_api.py")
        print("   2. 局域网访问: 修改 .env 中的 PROXY_API_HOST\n")
        exit(1)
    
    # 获取随机代理
    print("1. 获取随机代理:")
    proxy = client.get_random()
    print(f"   {proxy}\n")
    
    # 获取最佳代理
    print("2. 获取最佳代理(前5个):")
    best_proxies = client.get_best(limit=5)
    for i, p in enumerate(best_proxies, 1):
        print(f"   {i}. {p}")
    print()
    
    # 获取统计信息
    print("3. 代理池统计:")
    stats = client.get_stats()
    data = stats['data']
    print(f"   总代理数: {data['total_proxies']}")
    print(f"   24小时活跃: {data['active_proxies_24h']}")
    print(f"   成功率: {data['success_rate_24h']*100:.1f}%\n")
    
    # 使用示例
    print("4. 在requests中使用:")
    print("   import requests")
    print("   proxies = client.as_requests_proxies()")
    print("   response = requests.get('http://httpbin.org/ip', proxies=proxies)")
