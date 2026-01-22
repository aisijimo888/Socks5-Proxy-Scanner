"""
Telegram Bot 模块
提供命令交互和状态查询功能
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime

try:
    from telebot.async_telebot import AsyncTeleBot
    from telebot import types
    TELEBOT_AVAILABLE = True
except ImportError:
    TELEBOT_AVAILABLE = False
    logging.warning("pyTelegramBotAPI 未安装，Telegram功能不可用")

from proxy_database import ProxyDatabase


class TelegramBot:
    """Telegram Bot管理器"""
    
    def __init__(self, token: str, db_path: str = "proxies.db"):
        """
        初始化Telegram Bot
        
        Args:
            token: Bot Token
            db_path: 数据库路径
        """
        if not TELEBOT_AVAILABLE:
            raise ImportError("请安装 pyTelegramBotAPI: pip install pyTelegramBotAPI")
        
        self.bot = AsyncTeleBot(token)
        self.db = ProxyDatabase(db_path)
        self.logger = logging.getLogger(__name__)
        
        self._register_handlers()
    
    def _register_handlers(self):
        """注册命令处理器"""
        
        @self.bot.message_handler(commands=['start', 'help'])
        async def send_welcome(message):
            """欢迎消息"""
            welcome_text = """
🤖 *SOCKS5代理扫描器 Bot*

可用命令:
/stats - 查看代理池统计
/best - 获取最佳代理(前10)
/update - 手动触发更新
/sources - 查看代理源状态
/health - 数据库健康检查
/help - 显示此帮助信息

💡 提示: 你也可以直接发送IP:端口格式查询单个代理的信息
            """
            await self.bot.reply_to(message, welcome_text, parse_mode='Markdown')
        
        @self.bot.message_handler(commands=['stats'])
        async def send_stats(message):
            """发送统计信息"""
            try:
                stats = self.db.get_database_stats()
                
                stats_text = f"""
📊 *代理池统计*

总代理数: `{stats['total_proxies']}`
24小时活跃: `{stats['active_proxies_24h']}`
总验证次数: `{stats['total_validations']}`
24小时成功率: `{stats['success_rate_24h']*100:.1f}%`

🌍 *国家分布 (Top 5)*
"""
                for country in stats['top_countries'][:5]:
                    stats_text += f"\n• {country['country']}: {country['count']}"
                
                await self.bot.reply_to(message, stats_text, parse_mode='Markdown')
                
            except Exception as e:
                self.logger.error(f"获取统计数据失败: {e}")
                await self.bot.reply_to(message, f"❌ 获取统计数据失败: {str(e)}")
        
        @self.bot.message_handler(commands=['best'])
        async def send_best_proxies(message):
            """发送最佳代理列表"""
            try:
                proxies = self.db.get_best_proxies(limit=10)
                
                if not proxies:
                    await self.bot.reply_to(message, "❌ 暂无可用代理")
                    return
                
                response = "🌟 *最佳代理 (Top 10)*\n\n"
                
                for i, proxy in enumerate(proxies, 1):
                    country = proxy.get('country') or '未知'
                    score = proxy.get('avg_score', 0)
                    success_rate = proxy.get('success_rate', 0) * 100
                    response_time = proxy.get('avg_response_time', 0)
                    
                    response += f"{i}. `{proxy['proxy_address']}`\n"
                    response += f"   📍 {country} | ⭐ {score:.1f} | "
                    response += f"✅ {success_rate:.0f}% | ⏱️ {response_time:.2f}s\n\n"
                
                await self.bot.reply_to(message, response, parse_mode='Markdown')
                
            except Exception as e:
                self.logger.error(f"获取最佳代理失败: {e}")
                await self.bot.reply_to(message, f"❌ 获取代理列表失败: {str(e)}")
        
        @self.bot.message_handler(commands=['sources'])
        async def send_sources(message):
            """发送代理源状态"""
            try:
                sources = self.db.get_source_health()
                
                if not sources:
                    await self.bot.reply_to(message, "❌ 暂无代理源数据")
                    return
                
                response = "📡 *代理源状态*\n\n"
                
                for source in sources[:10]:
                    url = source['source_url']
                    # 缩短URL
                    if len(url) > 40:
                        url = url[:37] + "..."
                    
                    status = "✅" if source['is_active'] else "❌"
                    success_rate = source.get('success_rate', 0) * 100
                    total_proxies = source.get('total_proxies_found', 0)
                    
                    response += f"{status} {url}\n"
                    response += f"   成功率: {success_rate:.0f}% | 代理数: {total_proxies}\n\n"
                
                await self.bot.reply_to(message, response, parse_mode='Markdown')
                
            except Exception as e:
                self.logger.error(f"获取代理源状态失败: {e}")
                await self.bot.reply_to(message, f"❌ 获取代理源状态失败: {str(e)}")
        
        @self.bot.message_handler(commands=['health'])
        async def send_health(message):
            """数据库健康检查"""
            try:
                # 执行清理
                deleted_validations, deleted_proxies = self.db.cleanup_old_records(days=30)
                
                health_text = f"""
🏥 *数据库健康检查*

清理完成:
• 删除验证记录: {deleted_validations}
• 删除过期代理: {deleted_proxies}

状态: ✅ 健康
                """
                
                await self.bot.reply_to(message, health_text, parse_mode='Markdown')
                
            except Exception as e:
                self.logger.error(f"健康检查失败: {e}")
                await self.bot.reply_to(message, f"❌ 健康检查失败: {str(e)}")
        
        @self.bot.message_handler(commands=['update'])
        async def trigger_update(message):
            """触发手动更新"""
            await self.bot.reply_to(
                message, 
                "⏳ 更新功能需要集成到主扫描器中\n"
                "请在服务器上运行扫描器进行更新"
            )
        
        @self.bot.message_handler(func=lambda message: True)
        async def handle_proxy_query(message):
            """处理代理查询"""
            text = message.text.strip()
            
            # 检查是否为IP:端口格式
            if ':' in text and len(text.split(':')) == 2:
                try:
                    stats = self.db.get_proxy_stats(text)
                    
                    if not stats:
                        await self.bot.reply_to(message, f"❌ 代理 `{text}` 不在数据库中", parse_mode='Markdown')
                        return
                    
                    response = f"""
🔍 *代理信息*

地址: `{stats['proxy_address']}`
国家: {stats.get('country') or '未知'}
城市: {stats.get('city') or '未知'}
ISP: {stats.get('isp') or '未知'}

📊 *统计*
总检查: {stats['total_checks']}
成功次数: {stats['success_count']}
成功率: {stats.get('success_rate', 0)*100:.1f}%
平均响应: {stats.get('avg_response_time', 0):.2f}s
平均评分: {stats.get('avg_score', 0):.1f}

⏰ *时间*
首次发现: {stats['first_seen']}
最后检查: {stats.get('last_check', 'N/A')}
                    """
                    
                    await self.bot.reply_to(message, response, parse_mode='Markdown')
                    
                except Exception as e:
                    self.logger.error(f"查询代理失败: {e}")
                    await self.bot.reply_to(message, f"❌ 查询失败: {str(e)}")
            else:
                await self.bot.reply_to(
                    message, 
                    "💡 请发送 IP:端口 格式查询代理信息\n或使用 /help 查看可用命令"
                )
    
    async def start_polling(self):
        """启动Bot轮询"""
        self.logger.info("Telegram Bot 启动中...")
        await self.bot.polling(non_stop=True)
    
    async def send_notification(self, chat_id: str, message: str):
        """发送通知消息"""
        try:
            await self.bot.send_message(chat_id, message, parse_mode='Markdown')
        except Exception as e:
            self.logger.error(f"发送通知失败: {e}")


def run_bot(token: str, db_path: str = "proxies.db"):
    """运行Telegram Bot"""
    bot = TelegramBot(token, db_path)
    asyncio.run(bot.start_polling())


if __name__ == "__main__":
    import sys
    from config_manager import ConfigManager
    
    # 加载配置
    config = ConfigManager()
    
    if not config.telegram_bot_token:
        print("错误: 未设置TELEGRAM_BOT_TOKEN")
        print("请在.env文件中配置或设置环境变量")
        sys.exit(1)
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 启动Bot
    run_bot(config.telegram_bot_token, config.database_path)
