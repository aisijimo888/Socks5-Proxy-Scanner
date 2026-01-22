"""
订阅链接生成器
支持多种代理客户端格式：Clash、V2Ray、ShadowRocket、通用格式
"""

import base64
import json
import yaml
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from proxy_database import ProxyDatabase


class SubscriptionGenerator:
    """订阅链接生成器"""
    
    def __init__(self, db_path: str = "proxies.db", output_dir: str = "subscribe"):
        self.db = ProxyDatabase(db_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def generate_all_formats(self, limit: int = 100, min_score: float = 1.0):
        """生成所有格式的订阅文件"""
        # 获取高质量代理
        proxies = self.db.get_best_proxies(
            limit=limit,
            min_checks=3,
            min_success_rate=0.6
        )
        
        # 过滤评分
        proxies = [p for p in proxies if p.get('avg_score', 0) >= min_score]
        
        if not proxies:
            self.logger.warning("没有符合条件的代理")
            return
        
        self.logger.info(f"生成订阅文件，共 {len(proxies)} 个代理")
        
        # 生成各种格式
        self.generate_clash_yaml(proxies)
        self.generate_v2ray_json(proxies)
        self.generate_base64(proxies)
        self.generate_plain_text(proxies)
        self.generate_shadowrocket(proxies)
        
        self.logger.info(f"所有订阅文件已生成到: {self.output_dir}")
    
    def generate_clash_yaml(self, proxies: List[Dict]):
        """生成 Clash YAML 格式订阅"""
        clash_proxies = []
        proxy_names = []
        
        for idx, proxy in enumerate(proxies, 1):
            ip, port = proxy['proxy_address'].split(':')
            country = proxy.get('country_code', 'UN')
            score = proxy.get('avg_score', 0)
            
            # 生成代理名称
            name = f"{country}_{idx:03d}_S{score:.1f}"
            proxy_names.append(name)
            
            # Clash 代理配置
            clash_proxy = {
                'name': name,
                'type': 'socks5',
                'server': ip,
                'port': int(port),
                'udp': True
            }
            clash_proxies.append(clash_proxy)
        
        # 构建完整的 Clash 配置
        clash_config = {
            'port': 7890,
            'socks-port': 7891,
            'allow-lan': False,
            'mode': 'Rule',
            'log-level': 'info',
            'external-controller': '127.0.0.1:9090',
            
            'proxies': clash_proxies,
            
            'proxy-groups': [
                {
                    'name': '🚀 代理选择',
                    'type': 'select',
                    'proxies': ['♻️ 自动选择', '🔰 故障转移'] + proxy_names
                },
                {
                    'name': '♻️ 自动选择',
                    'type': 'url-test',
                    'proxies': proxy_names,
                    'url': 'http://www.gstatic.com/generate_204',
                    'interval': 300
                },
                {
                    'name': '🔰 故障转移',
                    'type': 'fallback',
                    'proxies': proxy_names,
                    'url': 'http://www.gstatic.com/generate_204',
                    'interval': 300
                }
            ],
            
            'rules': [
                'DOMAIN-SUFFIX,google.com,🚀 代理选择',
                'DOMAIN-KEYWORD,google,🚀 代理选择',
                'DOMAIN-SUFFIX,youtube.com,🚀 代理选择',
                'DOMAIN-SUFFIX,facebook.com,🚀 代理选择',
                'DOMAIN-SUFFIX,twitter.com,🚀 代理选择',
                'GEOIP,CN,DIRECT',
                'MATCH,🚀 代理选择'
            ]
        }
        
        # 保存文件
        output_file = self.output_dir / 'clash.yaml'
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(clash_config, f, allow_unicode=True, sort_keys=False)
        
        self.logger.info(f"✅ Clash 订阅已生成: {output_file}")
    
    def generate_v2ray_json(self, proxies: List[Dict]):
        """生成 V2Ray JSON 格式订阅"""
        v2ray_config = {
            'log': {
                'loglevel': 'warning'
            },
            'inbounds': [
                {
                    'port': 1080,
                    'protocol': 'socks',
                    'settings': {
                        'auth': 'noauth',
                        'udp': True
                    }
                }
            ],
            'outbounds': [],
            'routing': {
                'domainStrategy': 'IPOnDemand',
                'rules': [
                    {
                        'type': 'field',
                        'ip': ['geoip:private'],
                        'outboundTag': 'direct'
                    },
                    {
                        'type': 'field',
                        'domain': ['geosite:cn'],
                        'outboundTag': 'direct'
                    }
                ]
            }
        }
        
        # 添加代理出站
        for idx, proxy in enumerate(proxies):
            ip, port = proxy['proxy_address'].split(':')
            country = proxy.get('country_code', 'UN')
            
            outbound = {
                'tag': f'{country}_{idx:03d}',
                'protocol': 'socks',
                'settings': {
                    'servers': [
                        {
                            'address': ip,
                            'port': int(port)
                        }
                    ]
                }
            }
            v2ray_config['outbounds'].append(outbound)
        
        # 添加直连出站
        v2ray_config['outbounds'].append({
            'tag': 'direct',
            'protocol': 'freedom'
        })
        
        # 保存文件
        output_file = self.output_dir / 'v2ray.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(v2ray_config, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"✅ V2Ray 订阅已生成: {output_file}")
    
    def generate_base64(self, proxies: List[Dict]):
        """生成 Base64 编码的代理列表"""
        proxy_lines = []
        
        for proxy in proxies:
            # socks5://ip:port 格式
            proxy_url = f"socks5://{proxy['proxy_address']}"
            proxy_lines.append(proxy_url)
        
        # Base64 编码
        proxy_text = '\n'.join(proxy_lines)
        encoded = base64.b64encode(proxy_text.encode('utf-8')).decode('utf-8')
        
        # 保存文件
        output_file = self.output_dir / 'base64.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(encoded)
        
        self.logger.info(f"✅ Base64 订阅已生成: {output_file}")
    
    def generate_plain_text(self, proxies: List[Dict]):
        """生成纯文本代理列表"""
        output_file = self.output_dir / 'proxies.txt'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # 添加头部信息
            f.write(f"# SOCKS5 代理列表\n")
            f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 总数: {len(proxies)}\n")
            f.write(f"# 格式: socks5://IP:PORT\n\n")
            
            # 按国家分组
            by_country = {}
            for proxy in proxies:
                country = proxy.get('country', 'Unknown')
                country_code = proxy.get('country_code', 'UN')
                key = f"{country} ({country_code})"
                
                if key not in by_country:
                    by_country[key] = []
                by_country[key].append(proxy)
            
            # 写入代理
            for country, country_proxies in sorted(by_country.items()):
                f.write(f"\n# {country} - {len(country_proxies)} 个代理\n")
                for proxy in country_proxies:
                    score = proxy.get('avg_score', 0)
                    response_time = proxy.get('avg_response_time', 0)
                    f.write(f"socks5://{proxy['proxy_address']} # Score: {score:.1f}, RT: {response_time:.2f}s\n")
        
        self.logger.info(f"✅ 纯文本代理列表已生成: {output_file}")
    
    def generate_shadowrocket(self, proxies: List[Dict]):
        """生成 ShadowRocket 格式订阅"""
        sr_lines = []
        
        for idx, proxy in enumerate(proxies):
            ip, port = proxy['proxy_address'].split(':')
            country = proxy.get('country_code', 'UN')
            score = proxy.get('avg_score', 0)
            
            # ShadowRocket SOCKS5 格式
            # socks5://ip:port#备注
            name = f"{country}_{idx:03d}_S{score:.1f}"
            sr_line = f"socks5://{ip}:{port}#{name}"
            sr_lines.append(sr_line)
        
        # Base64 编码
        sr_text = '\n'.join(sr_lines)
        encoded = base64.b64encode(sr_text.encode('utf-8')).decode('utf-8')
        
        # 保存文件
        output_file = self.output_dir / 'shadowrocket.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(encoded)
        
        self.logger.info(f"✅ ShadowRocket 订阅已生成: {output_file}")
    
    def get_subscription_info(self) -> Dict:
        """获取订阅信息统计"""
        stats = self.db.get_database_stats()
        
        # 读取文件大小
        files_info = {}
        for file_name in ['clash.yaml', 'v2ray.json', 'base64.txt', 'proxies.txt', 'shadowrocket.txt']:
            file_path = self.output_dir / file_name
            if file_path.exists():
                size_kb = file_path.stat().st_size / 1024
                files_info[file_name] = {
                    'size_kb': round(size_kb, 2),
                    'path': str(file_path)
                }
        
        return {
            'total_proxies': stats.get('total_proxies', 0),
            'active_proxies': stats.get('active_proxies_24h', 0),
            'countries': stats.get('country_distribution', {}),
            'files': files_info,
            'update_time': datetime.now().isoformat()
        }


def main():
    """主函数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("="*60)
    print("订阅链接生成器")
    print("="*60)
    
    generator = SubscriptionGenerator()
    
    # 生成所有格式
    generator.generate_all_formats(limit=200, min_score=1.0)
    
    # 显示统计信息
    info = generator.get_subscription_info()
    print(f"\n📊 订阅统计:")
    print(f"  总代理数: {info['total_proxies']}")
    print(f"  活跃代理: {info['active_proxies']}")
    print(f"\n📁 生成的文件:")
    for file_name, file_info in info['files'].items():
        print(f"  ✅ {file_name} ({file_info['size_kb']} KB)")
    
    print(f"\n✨ 完成！订阅文件已保存到 subscribe/ 目录")


if __name__ == '__main__':
    main()
