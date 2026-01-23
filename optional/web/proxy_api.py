"""
代理API服务器
提供HTTP API接口供其他项目调用代理
"""

import os
import sys
import random
import logging
from datetime import datetime
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from proxy_database import ProxyDatabase
from config_manager import ConfigManager
from timezone_utils import now_utc

app = Flask(__name__)
CORS(app)

# 配置
config = ConfigManager()
db = ProxyDatabase(config.database_path)
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    """API首页"""
    return jsonify({
        'name': 'SOCKS5 Proxy API',
        'version': '1.0.0',
        'endpoints': {
            'random': '/api/proxy/random',
            'best': '/api/proxy/best',
            'by_country': '/api/proxy/country/<code>',
            'validate': '/api/proxy/validate',
            'stats': '/api/stats',
            'export': '/api/export/<format>',
            'subscribe_clash': '/api/subscribe/clash',
            'subscribe_v2ray': '/api/subscribe/v2ray',
            'subscribe_base64': '/api/subscribe/base64',
            'subscribe_shadowrocket': '/api/subscribe/shadowrocket'
        },
        'docs': 'https://github.com/yourname/proxy-scanner'
    })



@app.route('/api/proxy/random')
def get_random_proxy():
    """
    获取随机代理
    
    Query Parameters:
        country (str): 国家代码过滤 (可选)
        min_score (float): 最低评分 (可选, 默认0)
    
    Returns:
        {
            "address": "1.2.3.4:1080",
            "country": "US",
            "score": 85.5,
            "success_rate": 0.95,
            "format": "socks5://1.2.3.4:1080"
        }
    """
    try:
        # 获取参数
        country = request.args.get('country')
        min_score = request.args.get('min_score', 0, type=float)
        
        # 获取代理列表
        proxies = db.get_best_proxies(limit=100, min_checks=2, min_success_rate=0.5)
        
        # 过滤
        if country:
            proxies = [p for p in proxies if p.get('country_code') == country.upper()]
        
        if min_score > 0:
            proxies = [p for p in proxies if p.get('avg_score', 0) >= min_score]
        
        if not proxies:
            return jsonify({'error': 'No proxies available'}), 404
        
        # 随机选择
        proxy = random.choice(proxies)
        
        return jsonify({
            'address': proxy['proxy_address'],
            'country': proxy.get('country'),
            'country_code': proxy.get('country_code'),
            'city': proxy.get('city'),
            'score': round(proxy.get('avg_score', 0), 2),
            'success_rate': round(proxy.get('success_rate', 0), 3),
            'response_time': round(proxy.get('avg_response_time', 0), 3),
            'checks': proxy.get('total_checks', 0),
            'format': f"socks5://{proxy['proxy_address']}"
        })
        
    except Exception as e:
        logger.error(f"获取随机代理失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/proxy/best')
def get_best_proxies():
    """
    获取最佳代理列表
    
    Query Parameters:
        limit (int): 返回数量 (默认10, 最大100)
        country (str): 国家代码过滤 (可选)
        min_score (float): 最低评分 (可选)
        format (str): 返回格式 simple|detailed (默认simple)
    
    Returns:
        {
            "count": 10,
            "proxies": ["1.2.3.4:1080", ...]  // simple格式
        }
        或
        {
            "count": 10,
            "proxies": [{...}, {...}]  // detailed格式
        }
    """
    try:
        # 获取参数
        limit = min(request.args.get('limit', 10, type=int), 100)
        country = request.args.get('country')
        min_score = request.args.get('min_score', 0, type=float)
        format_type = request.args.get('format', 'simple')
        
        # 获取代理
        proxies = db.get_best_proxies(limit=limit * 2, min_checks=2, min_success_rate=0.5)
        
        # 过滤
        if country:
            proxies = [p for p in proxies if p.get('country_code') == country.upper()]
        
        if min_score > 0:
            proxies = [p for p in proxies if p.get('avg_score', 0) >= min_score]
        
        # 限制数量
        proxies = proxies[:limit]
        
        if not proxies:
            return jsonify({'error': 'No proxies available'}), 404
        
        # 格式化返回
        if format_type == 'simple':
            return jsonify({
                'count': len(proxies),
                'proxies': [p['proxy_address'] for p in proxies]
            })
        else:
            return jsonify({
                'count': len(proxies),
                'proxies': [{
                    'address': p['proxy_address'],
                    'country': p.get('country'),
                    'country_code': p.get('country_code'),
                    'score': round(p.get('avg_score', 0), 2),
                    'success_rate': round(p.get('success_rate', 0), 3),
                    'response_time': round(p.get('avg_response_time', 0), 3),
                } for p in proxies]
            })
        
    except Exception as e:
        logger.error(f"获取最佳代理失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/proxy/country/<country_code>')
def get_proxies_by_country(country_code):
    """
    获取指定国家的代理
    
    Path Parameters:
        country_code (str): 国家代码 (如 US, JP, DE)
    
    Query Parameters:
        limit (int): 返回数量 (默认10)
    """
    try:
        limit = min(request.args.get('limit', 10, type=int), 100)
        
        # 获取所有代理并过滤
        proxies = db.get_best_proxies(limit=1000, min_checks=2)
        country_proxies = [
            p for p in proxies 
            if p.get('country_code') == country_code.upper()
        ][:limit]
        
        if not country_proxies:
            return jsonify({'error': f'No proxies for country {country_code}'}), 404
        
        return jsonify({
            'country': country_code.upper(),
            'count': len(country_proxies),
            'proxies': [p['proxy_address'] for p in country_proxies]
        })
        
    except Exception as e:
        logger.error(f"获取国家代理失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/proxy/validate')
def validate_proxy():
    """
    验证代理状态
    
    Query Parameters:
        proxy (str): 代理地址 (格式: IP:PORT)
    """
    try:
        proxy = request.args.get('proxy')
        if not proxy:
            return jsonify({'error': 'Missing proxy parameter'}), 400
        
        stats = db.get_proxy_stats(proxy)
        
        return jsonify({
            'valid': stats is not None,
            'proxy': proxy,
            'stats': stats if stats else None
        })
        
    except Exception as e:
        logger.error(f"验证代理失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats')
def get_stats():
    """获取代理池统计信息"""
    try:
        stats = db.get_database_stats()
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': now_utc().isoformat()
        })
    except Exception as e:
        logger.error(f"获取统计失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/<format_type>')
def export_proxies(format_type):
    """
    导出代理列表
    
    Path Parameters:
        format_type: txt | json | csv
    
    Query Parameters:
        limit (int): 导出数量 (默认100)
    """
    try:
        limit = min(request.args.get('limit', 100, type=int), 1000)
        proxies = db.get_best_proxies(limit=limit)
        
        if format_type == 'txt':
            content = '\n'.join([p['proxy_address'] for p in proxies])
            return content, 200, {
                'Content-Type': 'text/plain; charset=utf-8',
                'Content-Disposition': 'attachment; filename=proxies.txt'
            }
        
        elif format_type == 'json':
            return jsonify({
                'count': len(proxies),
                'timestamp': now_utc().isoformat(),
                'proxies': [
                    {
                        'address': p['proxy_address'],
                        'country': p.get('country'),
                        'score': p.get('avg_score')
                    } for p in proxies
                ]
            })
        
        elif format_type == 'csv':
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['address', 'country', 'score', 'success_rate'])
            
            for p in proxies:
                writer.writerow([
                    p['proxy_address'],
                    p.get('country', ''),
                    p.get('avg_score', 0),
                    p.get('success_rate', 0)
                ])
            
            return output.getvalue(), 200, {
                'Content-Type': 'text/csv; charset=utf-8',
                'Content-Disposition': 'attachment; filename=proxies.csv'
            }
        
        else:
            return jsonify({'error': 'Invalid format'}), 400
        
    except Exception as e:
        logger.error(f"导出失败: {e}")
        return jsonify({'error': str(e)}), 500




@app.route('/api/subscribe/clash')
def subscribe_clash():
    """
    获取 Clash 订阅
    
    Returns:
        Clash YAML 格式的订阅文件
    """
    try:
        from pathlib import Path
        subscribe_file = Path('subscribe') / 'clash.yaml'
        
        if not subscribe_file.exists():
            return jsonify({'error': 'Subscription file not found. Please run subscription_generator.py first.'}), 404
        
        return send_file(
            subscribe_file,
            mimetype='text/yaml',
            as_attachment=True,
            download_name='clash.yaml'
        )
    except Exception as e:
        logger.error(f"获取 Clash 订阅失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/subscribe/v2ray')
def subscribe_v2ray():
    """
    获取 V2Ray 订阅
    
    Returns:
        V2Ray JSON 格式的订阅文件
    """
    try:
        from pathlib import Path
        subscribe_file = Path('subscribe') / 'v2ray.json'
        
        if not subscribe_file.exists():
            return jsonify({'error': 'Subscription file not found. Please run subscription_generator.py first.'}), 404
        
        return send_file(
            subscribe_file,
            mimetype='application/json',
            as_attachment=True,
            download_name='v2ray.json'
        )
    except Exception as e:
        logger.error(f"获取 V2Ray 订阅失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/subscribe/base64')
def subscribe_base64():
    """
    获取 Base64 订阅
    
    Returns:
        Base64 编码的代理列表
    """
    try:
        from pathlib import Path
        subscribe_file = Path('subscribe') / 'base64.txt'
        
        if not subscribe_file.exists():
            return jsonify({'error': 'Subscription file not found. Please run subscription_generator.py first.'}), 404
        
        return send_file(
            subscribe_file,
            mimetype='text/plain',
            as_attachment=False  # 直接显示内容
        )
    except Exception as e:
        logger.error(f"获取 Base64 订阅失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/subscribe/shadowrocket')
def subscribe_shadowrocket():
    """
    获取 ShadowRocket 订阅
    
    Returns:
        ShadowRocket 格式的订阅文件
    """
    try:
        from pathlib import Path
        subscribe_file = Path('subscribe') / 'shadowrocket.txt'
        
        if not subscribe_file.exists():
            return jsonify({'error': 'Subscription file not found. Please run subscription_generator.py first.'}), 404
        
        return send_file(
            subscribe_file,
            mimetype='text/plain',
            as_attachment=False  # 直接显示内容
        )
    except Exception as e:
        logger.error(f"获取 ShadowRocket 订阅失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/subscribe/plain')
def subscribe_plain():
    """
    获取纯文本代理列表
    
    Returns:
        纯文本格式的代理列表
    """
    try:
        from pathlib import Path
        subscribe_file = Path('subscribe') / 'proxies.txt'
        
        if not subscribe_file.exists():
            return jsonify({'error': 'Subscription file not found. Please run subscription_generator.py first.'}), 404
        
        return send_file(
            subscribe_file,
            mimetype='text/plain',
            as_attachment=False
        )
    except Exception as e:
        logger.error(f"获取纯文本订阅失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health')

def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': now_utc().isoformat(),
        'database': db.db_path,
        'total_proxies': db.get_database_stats().get('total_proxies', 0)
    })


def run_api_server(host='0.0.0.0', port=8080, debug=False):
    """启动API服务器"""
    logger.info(f"代理API服务器启动于 http://{host}:{port}")
    print(f"\n{'='*60}")
    print(f"代理API服务器启动成功！")
    print(f"{'='*60}")
    print(f"API地址: http://localhost:{port}")
    print(f"文档: http://localhost:{port}")
    print(f"{'='*60}\n")
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    run_api_server()
