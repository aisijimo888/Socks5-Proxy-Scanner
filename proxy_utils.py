"""
代理工具模块
提供共享的代理验证和处理函数
"""

import re
from typing import Tuple, Optional


def is_valid_proxy_format(proxy: str, allow_private: bool = False, allow_auth: bool = True) -> bool:
    """
    验证代理地址格式
    
    支持格式:
    - IP:PORT (如 1.2.3.4:1080)
    - USER:PASS@IP:PORT (如果 allow_auth=True)
    
    Args:
        proxy: 代理地址字符串
        allow_private: 是否允许私有IP地址 (10.x, 192.168.x, 172.16-31.x)
        allow_auth: 是否允许认证格式 (USER:PASS@IP:PORT)
    
    Returns:
        bool: 格式是否有效
    
    Examples:
        >>> is_valid_proxy_format("1.2.3.4:1080")
        True
        >>> is_valid_proxy_format("192.168.1.1:8080")
        False
        >>> is_valid_proxy_format("192.168.1.1:8080", allow_private=True)
        True
        >>> is_valid_proxy_format("user:pass@1.2.3.4:1080")
        True
    """
    try:
        # 处理认证格式
        if '@' in proxy:
            if not allow_auth:
                return False
            # 分离认证信息和地址
            _, address = proxy.rsplit('@', 1)
            proxy = address
        
        # 分离 IP 和端口
        parts = proxy.split(':')
        if len(parts) != 2:
            return False
        
        ip, port_str = parts
        
        # 验证 IP 地址
        ip_parts = ip.split('.')
        if len(ip_parts) != 4:
            return False
        
        # 检查每个 IP 段
        for part in ip_parts:
            if not part.isdigit():
                return False
            num = int(part)
            if not 0 <= num <= 255:
                return False
        
        # 排除私有 IP（如果不允许）
        if not allow_private:
            first = int(ip_parts[0])
            second = int(ip_parts[1]) if len(ip_parts) >= 2 else 0
            
            # 排除 10.x.x.x
            if first == 10:
                return False
            
            # 排除 127.x.x.x (loopback)
            if first == 127:
                return False
            
            # 排除 0.x.x.x
            if first == 0:
                return False
            
            # 排除 172.16.x.x - 172.31.x.x
            if first == 172 and 16 <= second <= 31:
                return False
            
            # 排除 192.168.x.x
            if first == 192 and second == 168:
                return False
        
        # 验证端口
        if not port_str.isdigit():
            return False
        port = int(port_str)
        if not 1 <= port <= 65535:
            return False
        
        return True
        
    except (ValueError, IndexError, AttributeError):
        return False


def parse_proxy_address(proxy: str) -> Tuple[Optional[str], Optional[int], Optional[Tuple[str, str]]]:
    """
    解析代理地址，提取 IP、端口和认证信息
    
    Args:
        proxy: 代理地址字符串
    
    Returns:
        Tuple[ip, port, (username, password) or None]
        如果解析失败返回 (None, None, None)
    
    Examples:
        >>> parse_proxy_address("1.2.3.4:1080")
        ('1.2.3.4', 1080, None)
        >>> parse_proxy_address("user:pass@1.2.3.4:1080")
        ('1.2.3.4', 1080, ('user', 'pass'))
    """
    try:
        auth = None
        
        # 处理认证格式
        if '@' in proxy:
            auth_part, address = proxy.rsplit('@', 1)
            if ':' in auth_part:
                username, password = auth_part.split(':', 1)
                auth = (username, password)
            proxy = address
        
        # 分离 IP 和端口
        ip, port_str = proxy.split(':')
        port = int(port_str)
        
        # 验证格式
        if not is_valid_proxy_format(proxy if not auth else f"{auth[0]}:{auth[1]}@{ip}:{port}"):
            return None, None, None
        
        return ip, port, auth
        
    except (ValueError, IndexError):
        return None, None, None


def format_proxy_url(proxy: str, protocol: str = 'socks5') -> Optional[str]:
    """
    将代理地址格式化为 URL 格式
    
    Args:
        proxy: 代理地址 (支持 IP:PORT 或 USER:PASS@IP:PORT)
        protocol: 协议类型 (socks5, socks4, http)
    
    Returns:
        格式化的代理URL，失败返回 None
    
    Examples:
        >>> format_proxy_url("1.2.3.4:1080")
        'socks5://1.2.3.4:1080'
        >>> format_proxy_url("user:pass@1.2.3.4:1080", "http")
        'http://user:pass@1.2.3.4:1080'
    """
    if not is_valid_proxy_format(proxy):
        return None
    
    if '@' in proxy:
        # 认证代理
        return f"{protocol}://{proxy}"
    else:
        # 普通代理
        return f"{protocol}://{proxy}"


def extract_proxies_from_text(text: str, allow_private: bool = False) -> set:
    """
    从文本中提取所有代理地址
    
    Args:
        text: 包含代理的文本
        allow_private: 是否允许私有IP
    
    Returns:
        提取到的代理地址集合
    
    Examples:
        >>> text = "使用这些代理: 1.2.3.4:1080, 5.6.7.8:8080"
        >>> extract_proxies_from_text(text)
        {'1.2.3.4:1080', '5.6.7.8:8080'}
    """
    # IP:端口正则表达式
    ip_port_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b'
    
    # 提取所有匹配
    matches = re.findall(ip_port_pattern, text)
    
    # 验证并去重
    valid_proxies = set()
    for match in matches:
        if is_valid_proxy_format(match, allow_private=allow_private):
            valid_proxies.add(match)
    
    return valid_proxies


def normalize_proxy_address(proxy: str) -> Optional[str]:
    """
    标准化代理地址（移除认证信息，返回 IP:PORT）
    
    Args:
        proxy: 代理地址
    
    Returns:
        标准化的 IP:PORT 格式，失败返回 None
    
    Examples:
        >>> normalize_proxy_address("user:pass@1.2.3.4:1080")
        '1.2.3.4:1080'
        >>> normalize_proxy_address("1.2.3.4:1080")
        '1.2.3.4:1080'
    """
    ip, port, _ = parse_proxy_address(proxy)
    if ip and port:
        return f"{ip}:{port}"
    return None
