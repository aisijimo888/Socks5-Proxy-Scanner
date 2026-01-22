@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║   SOCKS5代理扫描器 - 快速启动                         ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo [1/3] 检查依赖...
python check_dependencies.py
if errorlevel 1 (
    echo.
    echo ❌ 依赖检查失败！请先安装依赖。
    echo.
    echo 运行: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo [2/3] 启动增强扫描器...
echo 使用配置: 10秒超时, 50并发, 启用黑名单
echo.

python proxy_scanner_enhanced.py --timeout 10 --max-concurrency 50 --enable-blacklist --auto-blacklist

if errorlevel 1 (
    echo.
    echo ❌ 扫描失败！
    pause
    exit /b 1
)

echo.
echo [3/3] 扫描完成！
echo.
echo ✅ 结果文件:
echo    - proxies.json  (详细信息)
echo    - proxies.txt   (代理列表)
echo    - best_proxies.txt (最佳代理)
echo    - proxies.db    (数据库)
echo.
echo 💡 下一步:
echo    - 查看Web界面: python web_dashboard.py
echo    - 启动Telegram Bot: python telegram_bot.py
echo.

pause
