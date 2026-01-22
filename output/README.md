# Output Directory

此目录用于存放代理扫描结果。

## 📁 文件说明

扫描后会生成以下文件：

- `proxies.json` - 详细的代理信息（JSON格式）
- `proxies.txt` - 纯代理地址列表
- `proxies.csv` - CSV格式数据
- `best_proxies.txt` - 最佳代理列表
- `proxies.db` - SQLite数据库

## 🚫 Git忽略

此目录已添加到 `.gitignore`，不会上传到GitHub。

## 💡 使用方法

```bash
# 扫描后，结果自动保存到此目录
python proxy_scanner_enhanced.py

# 查看结果
cat output/best_proxies.txt
```
