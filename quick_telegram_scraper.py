"""
快速抓取 Telegram 频道代理
使用简化版抓取器，无需 API 认证
"""

import asyncio
import logging
from telegram_scraper import SimpleTelegramScraper

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 推荐的 SOCKS5 频道列表
TELEGRAM_CHANNELS = [
    'socks5list',           # 专注 SOCKS5，更新频繁
    'proxy_mtm',            # MTProto 代理
    'free_proxy_vpn',       # 免费代理混合
    'proxies_list',         # 各类代理
    'socks5_channel',       # SOCKS5 频道
]


async def scrape_telegram_channels(output_file='telegram_socks5.txt'):
    """
    从 Telegram 频道抓取代理
    
    Args:
        output_file: 输出文件路径
    """
    print("=" * 60)
    print("Telegram 频道代理抓取器")
    print("=" * 60)
    
    scraper = SimpleTelegramScraper()
    all_proxies = set()
    
    for channel in TELEGRAM_CHANNELS:
        print(f"\n正在抓取频道: @{channel}")
        try:
            proxies = await scraper.scrape_channel_messages(channel)
            all_proxies.update(proxies)
            print(f"✅ 从 @{channel} 获取到 {len(proxies)} 个代理")
        except Exception as e:
            print(f"❌ 抓取 @{channel} 失败: {e}")
    
    # 保存结果
    if all_proxies:
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入头部信息
            f.write(f"# Telegram 频道代理池\n")
            f.write(f"# 抓取时间: {asyncio.get_event_loop().time()}\n")
            f.write(f"# 总数: {len(all_proxies)}\n\n")
            
            # 写入代理
            for proxy in sorted(all_proxies):
                f.write(f"{proxy}\n")
        
        print("\n" + "=" * 60)
        print(f"✅ 成功！总计抓取到 {len(all_proxies)} 个代理")
        print(f"📁 已保存到: {output_file}")
        print("=" * 60)
        
        # 显示统计
        print("\n📊 频道统计:")
        print(f"  抓取频道数: {len(TELEGRAM_CHANNELS)}")
        print(f"  获取代理数: {len(all_proxies)}")
        print(f"  平均每频道: {len(all_proxies) // len(TELEGRAM_CHANNELS)}")
        
    else:
        print("\n⚠️ 警告：未获取到任何代理")
        print("   请检查：")
        print("   1. 网络连接是否正常")
        print("   2. 频道是否存在")
        print("   3. 频道是否有代理信息")
    
    return all_proxies


async def main():
    """主函数"""
    try:
        proxies = await scrape_telegram_channels()
        
        # 可选：自动验证代理
        print("\n💡 提示：")
        print("  下一步可以运行代理验证器验证这些代理:")
        print("  python proxy_scanner_enhanced.py")
        
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
