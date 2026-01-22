@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║   启动代理API服务器                                        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo [1/2] 检查数据库...
if not exist "proxies.db" (
    if not exist "output\proxies.db" (
        echo.
        echo ❌ 未找到代理数据库文件！
        echo.
        echo 请先运行扫描:
        echo    python proxy_scanner_enhanced.py
        echo.
        pause
        exit /b 1
    )
)

echo ✅ 数据库就绪
echo.

echo [2/2] 启动API服务器...
echo.
echo 💡 API地址: http://localhost:8080
echo 💡 文档: http://localhost:8080
echo.
echo 按 Ctrl+C 停止服务器
echo.
echo ============================================================
echo.

python proxy_api.py

pause
