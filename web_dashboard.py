"""
Web Dashboard - Flask后端
提供实时代理池监控和API接口
"""

import json
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

from proxy_database import ProxyDatabase
from config_manager import ConfigManager
from timezone_utils import now_utc


# 初始化Flask应用
app = Flask(__name__)
CORS(app)  # 启用CORS


# 全局配置和数据库
config = ConfigManager()
db = ProxyDatabase(config.database_path)
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/stats')
def get_stats():
    """获取代理池统计数据"""
    try:
        stats = db.get_database_stats()
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': now_utc().isoformat()
        })
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/proxies')
def get_proxies():
    """获取代理列表"""
    try:
        # 获取参数
        limit = request.args.get('limit', 50, type=int)
        min_checks = request.args.get('min_checks', 3, type=int)
        min_success_rate = request.args.get('min_success_rate', 0.5, type=float)
        
        proxies = db.get_best_proxies(
            limit=limit,
            min_checks=min_checks,
            min_success_rate=min_success_rate
        )
        
        return jsonify({
            'success': True,
            'data': proxies,
            'count': len(proxies),
            'timestamp': now_utc().isoformat()
        })
    except Exception as e:
        logger.error(f"获取代理列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/proxy/<path:proxy_address>')
def get_proxy_detail(proxy_address):
    """获取单个代理详情"""
    try:
        stats = db.get_proxy_stats(proxy_address)
        
        if not stats:
            return jsonify({
                'success': False,
                'error': '代理不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': now_utc().isoformat()
        })
    except Exception as e:
        logger.error(f"获取代理详情失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sources')
def get_sources():
    """获取代理源状态"""
    try:
        sources = db.get_source_health()
        
        return jsonify({
            'success': True,
            'data': sources,
            'count': len(sources),
            'timestamp': now_utc().isoformat()
        })
    except Exception as e:
        logger.error(f"获取代理源状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/active_proxies')
def get_active_proxies():
    """获取最近活跃的代理"""
    try:
        hours = request.args.get('hours', 24, type=int)
        proxies = db.get_all_active_proxies(hours=hours)
        
        return jsonify({
            'success': True,
            'data': proxies,
            'count': len(proxies),
            'timestamp': now_utc().isoformat()
        })
    except Exception as e:
        logger.error(f"获取活跃代理失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cleanup', methods=['POST'])
def trigger_cleanup():
    """触发数据库清理"""
    try:
        days = request.json.get('days', 30) if request.json else 30
        deleted_validations, deleted_proxies = db.cleanup_old_records(days=days)
        
        return jsonify({
            'success': True,
            'data': {
                'deleted_validations': deleted_validations,
                'deleted_proxies': deleted_proxies
            },
            'timestamp': now_utc().isoformat()
        })
    except Exception as e:
        logger.error(f"数据库清理失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/export')
def export_proxies():
    """导出代理列表"""
    try:
        format_type = request.args.get('format', 'json')
        proxies = db.get_best_proxies(limit=1000)
        
        if format_type == 'txt':
            # 纯文本格式
            text = '\n'.join([p['proxy_address'] for p in proxies])
            return text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
        elif format_type == 'csv':
            # CSV格式
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=proxies[0].keys() if proxies else [])
            writer.writeheader()
            writer.writerows(proxies)
            
            return output.getvalue(), 200, {'Content-Type': 'text/csv; charset=utf-8'}
        
        else:
            # JSON格式 (默认)
            return jsonify({
                'success': True,
                'data': proxies,
                'count': len(proxies),
                'timestamp': now_utc().isoformat()
            })
            
    except Exception as e:
        logger.error(f"导出失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health')
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'timestamp': now_utc().isoformat()
    })


def run_server(host: str = None, port: int = None, debug: bool = None):
    """
    启动Web服务器
    
    Args:
        host: 主机地址
        port: 端口
        debug: 调试模式
    """
    host = host or config.web_host if hasattr(config, 'web_host') else '0.0.0.0'  # 0.0.0.0 允许局域网访问
    port = port or config.web_port
    debug = debug if debug is not None else config.web_debug
    
    print(f"\n{'='*60}")
    print(f"Web Dashboard 启动成功！")
    print(f"{'='*60}")
    print(f"本地访问: http://localhost:{port}")
    print(f"局域网访问: http://你的IP地址:{port}")
    print(f"{'='*60}\n")
    
    logger.info(f"Web Dashboard 启动于 http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 启动服务器
    run_server()
