"""
配置管理模块
统一管理环境变量和配置
"""

import os
from typing import Optional, List
from dotenv import load_dotenv
import logging


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, env_file: str = ".env"):
        """
        初始化配置管理器
        
        Args:
            env_file: 环境变量文件路径
        """
        # 加载环境变量
        if os.path.exists(env_file):
            load_dotenv(env_file)
            logging.info(f"已加载环境变量文件: {env_file}")
        else:
            logging.warning(f"环境变量文件不存在: {env_file}, 使用默认配置")
    
    # Telegram配置
    @property
    def telegram_bot_token(self) -> Optional[str]:
        """Telegram Bot Token"""
        return os.getenv("TELEGRAM_BOT_TOKEN")
    
    @property
    def telegram_chat_id(self) -> Optional[str]:
        """Telegram Chat ID"""
        return os.getenv("TELEGRAM_CHAT_ID")
    
    @property
    def telegram_channels(self) -> List[str]:
        """Telegram频道列表"""
        channels_str = os.getenv("TELEGRAM_CHANNELS", "@socks5list,@proxy_mtm,@free_proxy_vpn")
        return [ch.strip() for ch in channels_str.split(',') if ch.strip()]
    
    # 数据库配置
    @property
    def database_path(self) -> str:
        """数据库文件路径"""
        return os.getenv("DATABASE_PATH", "proxies.db")
    
    @property
    def cleanup_days(self) -> int:
        """数据清理天数"""
        try:
            return int(os.getenv("CLEANUP_DAYS", "30"))
        except ValueError:
            return 30
    
    # Web配置
    @property
    def web_port(self) -> int:
        """Web服务端口"""
        try:
            return int(os.getenv("WEB_PORT", "5000"))
        except ValueError:
            return 5000
    
    @property
    def web_host(self) -> str:
        """Web服务主机"""
        return os.getenv("WEB_HOST", "0.0.0.0")
    
    @property
    def web_debug(self) -> bool:
        """Web调试模式"""
        return os.getenv("WEB_DEBUG", "False").lower() == "true"
    
    # 扫描配置
    @property
    def scan_timeout(self) -> int:
        """扫描超时时间"""
        try:
            return int(os.getenv("SCAN_TIMEOUT", "10"))
        except ValueError:
            return 10
    
    @property
    def max_concurrency(self) -> int:
        """最大并发数"""
        try:
            return int(os.getenv("MAX_CONCURRENCY", "50"))
        except ValueError:
            return 50
    
    # 功能开关
    @property
    def enable_telegram(self) -> bool:
        """启用Telegram功能"""
        return os.getenv("ENABLE_TELEGRAM", "False").lower() == "true"
    
    @property
    def enable_web(self) -> bool:
        """启用Web Dashboard"""
        return os.getenv("ENABLE_WEB", "False").lower() == "true"
    
    @property
    def enable_dns_check(self) -> bool:
        """启用DNS泄露检测"""
        return os.getenv("ENABLE_DNS_CHECK", "False").lower() == "true"
    
    @property
    def enable_bandwidth_test(self) -> bool:
        """启用带宽测试"""
        return os.getenv("ENABLE_BANDWIDTH_TEST", "False").lower() == "true"
    
    # GitHub Actions配置
    @property
    def github_token(self) -> Optional[str]:
        """GitHub Token"""
        return os.getenv("GITHUB_TOKEN")
    
    @property
    def github_repository(self) -> Optional[str]:
        """GitHub Repository"""
        return os.getenv("GITHUB_REPOSITORY")
    
    def validate(self) -> bool:
        """
        验证配置
        
        Returns:
            配置是否有效
        """
        issues = []
        
        # 验证Telegram配置
        if self.enable_telegram:
            if not self.telegram_bot_token:
                issues.append("TELEGRAM_BOT_TOKEN未设置，但启用了Telegram功能")
        
        # 验证端口范围
        if not 1 <= self.web_port <= 65535:
            issues.append(f"WEB_PORT无效: {self.web_port}")
        
        # 验证数值范围
        if self.scan_timeout < 1:
            issues.append(f"SCAN_TIMEOUT无效: {self.scan_timeout}")
        
        if self.max_concurrency < 1:
            issues.append(f"MAX_CONCURRENCY无效: {self.max_concurrency}")
        
        if self.cleanup_days < 1:
            issues.append(f"CLEANUP_DAYS无效: {self.cleanup_days}")
        
        # 输出问题
        if issues:
            for issue in issues:
                logging.error(f"配置错误: {issue}")
            return False
        
        logging.info("配置验证通过")
        return True
    
    def print_config(self):
        """打印当前配置（隐藏敏感信息）"""
        print("\n" + "=" * 50)
        print("当前配置")
        print("=" * 50)
        
        print(f"数据库路径: {self.database_path}")
        print(f"数据清理天数: {self.cleanup_days}")
        print(f"扫描超时: {self.scan_timeout}s")
        print(f"最大并发: {self.max_concurrency}")
        
        print(f"\n功能开关:")
        print(f"  Telegram: {'启用' if self.enable_telegram else '禁用'}")
        print(f"  Web Dashboard: {'启用' if self.enable_web else '禁用'}")
        print(f"  DNS检测: {'启用' if self.enable_dns_check else '禁用'}")
        print(f"  带宽测试: {'启用' if self.enable_bandwidth_test else '禁用'}")
        
        if self.enable_telegram:
            print(f"\nTelegram配置:")
            print(f"  Bot Token: {'已设置' if self.telegram_bot_token else '未设置'}")
            print(f"  Chat ID: {self.telegram_chat_id or '未设置'}")
            print(f"  监听频道: {', '.join(self.telegram_channels)}")
        
        if self.enable_web:
            print(f"\nWeb配置:")
            print(f"  主机: {self.web_host}")
            print(f"  端口: {self.web_port}")
            print(f"  调试模式: {'启用' if self.web_debug else '禁用'}")
        
        print("=" * 50 + "\n")
