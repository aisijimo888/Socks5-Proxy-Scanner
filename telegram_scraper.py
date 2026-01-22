"""
Telegram频道代理抓取器
从指定的Telegram频道抓取代理信息
"""

import asyncio
import re
import logging
from typing import List, Set
from datetime import datetime

try:
    from telethon import TelegramClient, events
    from telethon.tl.types import Channel
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    logging.warning("telethon 未安装，Telegram频道抓取功能不可用")


class TelegramScraper:
    """Telegram频道代理抓取器"""
    
    def __init__(self, api_id: int, api_hash: str, phone: str, session_name: str = "proxy_scraper"):
        """
        初始化Telegram客户端
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash  
            phone: 手机号
            session_name: 会话名称
        """
        if not TELETHON_AVAILABLE:
            raise ImportError("请安装 telethon: pip install telethon")
        
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.phone = phone
        self.logger = logging.getLogger(__name__)
        self.proxies_found = set()
    
    async def start(self):
        """启动客户端"""
        await self.client.start(phone=self.phone)
        self.logger.info("Telegram客户端已启动")
    
    async def scrape_channel(self, channel_username: str, limit: int = 100) -> Set[str]:
        """
        从频道抓取代理
        
        Args:
            channel_username: 频道用户名 (如 @socks5list)
            limit: 抓取消息数量限制
            
        Returns:
            代理集合
        """
        proxies = set()
        
        try:
            # IP:端口正则
            ip_port_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b'
            
            # 获取频道消息
            async for message in self.client.iter_messages(channel_username, limit=limit):
                if message.text:
                    # 提取所有IP:端口
                    matches = re.findall(ip_port_pattern, message.text)
                    for match in matches:
                        if self._is_valid_proxy(match):
                            proxies.add(match)
            
            self.logger.info(f"从频道 {channel_username} 抓取到 {len(proxies)} 个代理")
            
        except Exception as e:
            self.logger.error(f"抓取频道 {channel_username} 失败: {e}")
        
        return proxies
    
    async def scrape_multiple_channels(self, channels: List[str], limit: int = 100) -> Set[str]:
        """
        从多个频道抓取代理
        
        Args:
            channels: 频道列表
            limit: 每个频道的消息限制
        """
        all_proxies = set()
        
        for channel in channels:
            proxies = await self.scrape_channel(channel, limit)
            all_proxies.update(proxies)
        
        self.logger.info(f"总计从 {len(channels)} 个频道抓取到 {len(all_proxies)} 个代理")
        return all_proxies
    
    async def monitor_channels(self, channels: List[str], callback=None):
        """
        实时监听频道新消息
        
        Args:
            channels: 要监听的频道列表
            callback: 发现新代理时的回调函数
        """
        ip_port_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b'
        
        @self.client.on(events.NewMessage(chats=channels))
        async def handler(event):
            if event.message.text:
                matches = re.findall(ip_port_pattern, event.message.text)
                new_proxies = []
                
                for match in matches:
                    if self._is_valid_proxy(match) and match not in self.proxies_found:
                        self.proxies_found.add(match)
                        new_proxies.append(match)
                
                if new_proxies:
                    self.logger.info(f"发现 {len(new_proxies)} 个新代理")
                    if callback:
                        await callback(new_proxies)
        
        self.logger.info(f"开始监听 {len(channels)} 个频道...")
        await self.client.run_until_disconnected()
    
    def _is_valid_proxy(self, proxy: str) -> bool:
        """验证代理格式"""
        try:
            ip, port = proxy.split(':')
            
            # 验证IP
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            
            for part in parts:
                num = int(part)
                if not 0 <= num <= 255:
                    return False
            
            # 排除私有IP
            first = int(parts[0])
            if first in [10, 127, 0]:
                return False
            if first == 172 and 16 <= int(parts[1]) <= 31:
                return False
            if first == 192 and parts[1] == '168':
                return False
            
            # 验证端口
            port_num = int(port)
            if not 1 <= port_num <= 65535:
                return False
            
            return True
            
        except (ValueError, IndexError):
            return False
    
    async def close(self):
        """关闭客户端"""
        await self.client.disconnect()


# 简化版本: 使用Bot API而不是User API
class SimpleTelegramScraper:
    """简化的Telegram抓取器 - 使用公开频道"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def scrape_channel_messages(self, channel_url: str) -> Set[str]:
        """
        从公开频道抓取代理 (使用Web抓取)
        
        注意: 这是简化版本，实际效果有限
        建议使用完整的TelegramScraper类
        """
        import aiohttp
        
        proxies = set()
        ip_port_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b'
        
        try:
            # 尝试从Telegram Web预览抓取
            preview_url = f"https://t.me/s/{channel_url.replace('@', '')}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(preview_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        matches = re.findall(ip_port_pattern, html)
                        
                        for match in matches:
                            if self._is_valid_proxy(match):
                                proxies.add(match)
            
            self.logger.info(f"从 {channel_url} 抓取到 {len(proxies)} 个代理")
            
        except Exception as e:
            self.logger.error(f"抓取频道失败: {e}")
        
        return proxies
    
    def _is_valid_proxy(self, proxy: str) -> bool:
        """验证代理格式"""
        try:
            ip, port = proxy.split(':')
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            
            for part in parts:
                num = int(part)
                if not 0 <= num <= 255:
                    return False
            
            port_num = int(port)
            return 1 <= port_num <= 65535
            
        except:
            return False


if __name__ == "__main__":
    # 示例用法
    print("""
Telegram频道抓取器使用说明:

方式1 - 完整功能 (需要Telegram API):
1. 访问 https://my.telegram.org/apps 获取 API ID 和 API Hash
2. 使用TelegramScraper类进行抓取

方式2 - 简化版本 (仅公开频道):
使用SimpleTelegramScraper类，无需API认证

推荐的SOCKS5频道:
- @socks5list
- @proxy_mtm
- @free_proxy_vpn
- @proxies_list
- @socks5_channel
    """)
