"""
依赖检查脚本 - 检查所有必需的依赖和资源
"""

import sys
import os

def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    if sys.version_info < (3, 8):
        print("   ❌ Python版本过低！需要Python 3.8+")
        print(f"   当前版本: {sys.version}")
        return False
    print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def check_dependencies():
    """检查Python依赖包"""
    print("\n🔍 检查依赖包...")
    
    required_packages = {
        'aiohttp': '核心依赖',
        'aiohttp_socks': '代理连接',
        'python-dotenv': '环境变量',
    }
    
    optional_packages = {
        'flask': 'Web Dashboard',
        'telebot': 'Telegram Bot',
        'telethon': 'Telegram抓取',
        'plotly': '数据可视化',
    }
    
    missing_required = []
    missing_optional = []
    
    # 检查必需包
    for package, purpose in required_packages.items():
        try:
            if package == 'python-dotenv':
                __import__('dotenv')
            elif package == 'aiohttp_socks':
                __import__('aiohttp_socks')
            else:
                __import__(package)
            print(f"   ✅ {package:<20} ({purpose})")
        except ImportError:
            print(f"   ❌ {package:<20} ({purpose}) - 缺失！")
            missing_required.append(package)
    
    # 检查可选包
    for package, purpose in optional_packages.items():
        try:
            if package == 'telebot':
                __import__('telebot')
            else:
                __import__(package)
            print(f"   ✅ {package:<20} ({purpose}) - 可选")
        except ImportError:
            print(f"   ⚠️ {package:<20} ({purpose}) - 未安装 (可选)")
            missing_optional.append(package)
    
    if missing_required:
        print(f"\n❌ 缺少必需依赖: {', '.join(missing_required)}")
        print("\n安装方法:")
        print("   pip install -r requirements.txt")
        return False
    
    if missing_optional:
        print(f"\n⚠️ 缺少可选依赖: {', '.join(missing_optional)}")
        print("   这些功能将不可用，如需使用请安装:")
        print("   pip install -r requirements.txt")
    
    return True

def check_geoip_database():
    """检查GeoIP数据库"""
    print("\n🔍 检查GeoIP数据库...")
    
    if os.path.exists('GeoLite2-ASN.mmdb'):
        size_mb = os.path.getsize('GeoLite2-ASN.mmdb') / (1024 * 1024)
        print(f"   ✅ GeoLite2-ASN.mmdb ({size_mb:.1f} MB)")
        return True
    else:
        print("   ⚠️ GeoLite2-ASN.mmdb 不存在 (可选)")
        print("   影响: ISP类型检测可能不准确")
        print("   下载: https://dev.maxmind.com/geoip/geolite2-free-geolocation-data")
        return True  # 可选，不影响运行

def check_config_files():
    """检查配置文件"""
    print("\n🔍 检查配置文件...")
    
    has_env = os.path.exists('.env')
    has_env_example = os.path.exists('.env.example')
    
    if has_env:
        print("   ✅ .env 配置文件存在")
    elif has_env_example:
        print("   ⚠️ .env 不存在，但找到 .env.example")
        print("   建议: 复制 .env.example 为 .env 并配置")
    else:
        print("   ℹ️ 未找到配置文件 (将使用默认配置)")
    
    return True

def check_directory_structure():
    """检查目录结构"""
    print("\n🔍 检查目录结构...")
    
    required_dirs = []
    optional_dirs = ['templates', 'static', 'static/css', 'static/js']
    
    # 检查可选目录
    for dir_path in optional_dirs:
        if os.path.exists(dir_path):
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ⚠️ {dir_path} 不存在 (Web Dashboard不可用)")
    
    return True

def main():
    """主函数"""
    print("=" * 70)
    print("SOCKS5代理扫描器 - 依赖检查")
    print("=" * 70)
    
    checks = [
        ("Python版本", check_python_version),
        ("依赖包", check_dependencies),
        ("GeoIP数据库", check_geoip_database),
        ("配置文件", check_config_files),
        ("目录结构", check_directory_structure),
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(f"   ❌ 检查 {name} 时出错: {e}")
            all_passed = False
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print("✅ 所有检查通过！可以开始使用。")
        print("\n快速开始:")
        print("   python proxy_scanner_enhanced.py")
        print("=" * 70)
        return 0
    else:
        print("⚠️ 部分检查未通过，请先解决上述问题。")
        print("\n安装依赖:")
        print("   pip install -r requirements.txt")
        print("=" * 70)
        return 1

if __name__ == '__main__':
    sys.exit(main())
