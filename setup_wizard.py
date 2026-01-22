"""
首次运行向导 - 帮助用户快速配置项目
"""

import os
import sys
import subprocess

def welcome():
    """欢迎信息"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║   SOCKS5代理扫描器 - 首次运行向导                     ║
╚══════════════════════════════════════════════════════════════╝

欢迎使用！这个向导将帮助您完成初始配置。
    """)

def check_env_file():
    """检查并创建.env文件"""
    print("\n[步骤 1/4] 环境配置")
    print("=" * 60)
    
    if os.path.exists('.env'):
        print("✅ .env 文件已存在")
        return True
    
    if not os.path.exists('.env.example'):
        print("⚠️ 未找到 .env.example 模板")
        return False
    
    print("📝 创建 .env 配置文件...")
    print("\n是否创建.env文件？(Y/n): ", end='')
    choice = input().lower()
    
    if choice in ['', 'y', 'yes']:
        # 复制.env.example到.env
        with open('.env.example', 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 已创建 .env 文件")
        print("\n💡 提示: 如需使用Telegram功能，请编辑 .env 填入:")
        print("   - TELEGRAM_BOT_TOKEN")
        print("   - TELEGRAM_CHAT_ID")
        return True
    else:
        print("⏭️ 跳过配置文件创建")
        return False

def install_dependencies():
    """安装依赖"""
    print("\n[步骤 2/4] 安装依赖")
    print("=" * 60)
    
    print("是否立即安装依赖？(Y/n): ", end='')
    choice = input().lower()
    
    if choice in ['', 'y', 'yes']:
        print("\n📦 安装依赖中...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
            print("✅ 依赖安装完成")
            return True
        except subprocess.CalledProcessError:
            print("❌ 依赖安装失败")
            print("\n手动安装方法:")
            print("   pip install -r requirements.txt")
            return False
    else:
        print("⏭️ 跳过依赖安装")
        print("\n💡 请稍后手动运行:")
        print("   pip install -r requirements.txt")
        return False

def configure_whitelist():
    """配置国家白名单"""
    print("\n[步骤 3/4] 配置国家白名单")
    print("=" * 60)
    
    print("\n选择代理质量策略:")
    print("1. 高质量 (核心5国: 美日德新荷) - 成功率~80%")
    print("2. 平衡模式 (13国) - 成功率~60%, 数量更多 [默认]")
    print("3. 不限制 (所有国家) - 代理最多，质量参差")
    print("\n请选择 (1/2/3): ", end='')
    
    choice = input().strip()
    
    recommendations = {
        '1': "核心5国 - 追求质量",
        '2': "平衡13国 - 当前默认配置",
        '3': "不限制 - 追求数量"
    }
    
    selected = recommendations.get(choice, recommendations['2'])
    print(f"\n✅ 已选择: {selected}")
    
    if choice == '1':
        print("\n💡 提示: 如需修改，编辑 config.py 中的 target_countries")
        print("   只保留: United States, Japan, Germany, Singapore, Netherlands")
    elif choice == '3':
        print("\n💡 提示: 如需修改，编辑 config.py")
        print("   设置: target_countries = None")
    
    return True

def run_test_scan():
    """运行测试扫描"""
    print("\n[步骤 4/4] 测试运行")
    print("=" * 60)
    
    print("\n是否立即运行一次测试扫描？(y/N): ", end='')
    choice = input().lower()
    
    if choice in ['y', 'yes']:
        print("\n🚀 启动测试扫描 (30秒超时, 仅测试少量代理)...")
        print("=" * 60)
        
        try:
            # 运行demo的演示扫描
            subprocess.call([sys.executable, 'demo.py'])
            print("\n✅ 测试完成")
            return True
        except KeyboardInterrupt:
            print("\n\n⚠️ 测试中断")
            return False
    else:
        print("⏭️ 跳过测试运行")
        return False

def show_next_steps():
    """显示后续步骤"""
    print("\n" + "=" * 60)
    print("🎉 配置完成！")
    print("=" * 60)
    
    print("\n📚 快速开始:")
    print("\n1. 运行扫描:")
    print("   python proxy_scanner_enhanced.py")
    print("   或使用: start.bat")
    
    print("\n2. 启动Web界面:")
    print("   python web_dashboard.py")
    print("   访问: http://localhost:5000")
    
    print("\n3. 启动Telegram Bot (需配置):")
    print("   python telegram_bot.py")
    
    print("\n📖 更多文档:")
    print("   - README.md - 主文档")
    print("   - TIMEOUT_CONFIG_GUIDE.md - 超时配置")
    print("   - COUNTRY_WHITELIST_GUIDE.md - 国家白名单")
    print("   - WEB_DASHBOARD_GUIDE.md - Web界面")
    
    print("\n" + "=" * 60)

def main():
    """主函数"""
    try:
        welcome()
        
        # 执行配置步骤
        check_env_file()
        install_dependencies()
        configure_whitelist()
        run_test_scan()
        
        show_next_steps()
        
        print("\n按Enter退出...")
        input()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 向导已取消")
        return 1
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
