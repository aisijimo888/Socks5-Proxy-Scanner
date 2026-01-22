"""
订阅链接生成器
支持多种代理客户端格式：Clash、V2Ray、ShadowRocket、通用格式
"""

import base64
import json
import yaml
import logging
import os
from pathlib import Path
from typing import List, Dict
from datetime import datetime

class SubscriptionGenerator:
    """订阅链接生成器"""
    
    def __init__(self, json_path: str = "subscribe/proxies.json", output_dir: str = "subscribe"):
        self.json_path = json_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.proxies = self._load_proxies()
    
    def _load_proxies(self) -> List[Dict]:
        """从 JSON 文件加载代理"""
        if not os.path.exists(self.json_path):
            self.logger.warning(f"找不到代理文件: {self.json_path}")
            return []
        
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 处理新格式：包含metadata的包装结构
                if isinstance(data, dict) and 'proxies' in data:
                    return data['proxies']
                # 向后兼容：如果是旧的纯数组格式
                elif isinstance(data, list):
                    return data
                else:
                    self.logger.error(f"未知的JSON格式")
                    return []
        except Exception as e:
            self.logger.error(f"加载代理文件失败: {e}")
            return []
    
    def _get_score(self, proxy: Dict) -> float:
        """获取代理评分，兼容新旧格式"""
        # 优先使用新的rating系统
        if 'rating' in proxy and isinstance(proxy['rating'], dict):
            return proxy['rating'].get('overall_score', 0)
        # 向后兼容旧的score字段
        return proxy.get('score', 0)
    
    def generate_all_formats(self, min_score: float = 10.0):
        """生成所有格式的订阅文件"""
        # 过滤评分 (假设满分100，这里默认只取10分以上的，或者根据实际评分逻辑调整)
        # 注意：新的评分系统可能是 0-100 分制
        valid_proxies = [p for p in self.proxies if self._get_score(p) >= min_score]
        
        # 按分数排序
        valid_proxies.sort(key=lambda x: self._get_score(x), reverse=True)
        
        if not valid_proxies:
            self.logger.warning("没有符合条件的代理")
            return
        
        self.logger.info(f"生成订阅文件，共 {len(valid_proxies)} 个代理")
        
        # 生成各种格式
        self.generate_clash_yaml(valid_proxies)
        self.generate_v2ray_json(valid_proxies)
        self.generate_base64(valid_proxies)
        self.generate_plain_text(valid_proxies)
        self.generate_shadowrocket(valid_proxies)
        
        self.logger.info(f"所有订阅文件已生成到: {self.output_dir}")
    
    def generate_clash_yaml(self, proxies: List[Dict]):
        """生成 Clash YAML 格式订阅"""
        clash_proxies = []
        proxy_names = []
        
        for idx, proxy in enumerate(proxies, 1):
            # 兼容不同的字段名
            address = proxy.get('proxy', '') or f"{proxy.get('ip')}:{proxy.get('port')}"
            if ':' not in address:
                continue
                
            ip, port = address.split(':')
            country = proxy.get('country', 'UN')
            score = self._get_score(proxy)
            
            # 获取匿名性和速度等级（兼容新旧格式）
            if 'rating' in proxy and isinstance(proxy['rating'], dict):
                # 新格式
                anonymity = proxy['rating'].get('anonymity_level', 'Unknown')[:1]
                speed = proxy['rating'].get('speed_tier', 'Unknown')[:1]
            else:
                # 旧格式
                anonymity = proxy.get('anonymity_level', 'Unknown')[:1]  # E/A/T/U
                speed = proxy.get('speed_tier', 'Unknown')[:1]  # F/M/S/U
            
            # 生成增强的代理名称: Country_idx_Score_Anonymity_Speed
            name = f"{country}_{idx:03d}_S{int(score)}_{anonymity}{speed}"
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
            address = proxy.get('proxy', '') or f"{proxy.get('ip')}:{proxy.get('port')}"
            if ':' not in address:
                continue
                
            ip, port = address.split(':')
            country = proxy.get('country', 'UN')
            
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
            address = proxy.get('proxy', '') or f"{proxy.get('ip')}:{proxy.get('port')}"
            # socks5://ip:port 格式
            proxy_url = f"socks5://{address}"
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
                if country not in by_country:
                    by_country[country] = []
                by_country[country].append(proxy)
            
            # 写入代理
            for country, country_proxies in sorted(by_country.items()):
                f.write(f"\n# {country} - {len(country_proxies)} 个代理\n")
                for proxy in country_proxies:
                    address = proxy.get('proxy', '') or f"{proxy.get('ip')}:{proxy.get('port')}"
                    score = self._get_score(proxy)
                    response_time = proxy.get('response_time', 0)
                    f.write(f"socks5://{address} # Score: {score:.1f}, RT: {response_time:.2f}s\n")
        
        self.logger.info(f"✅ 纯文本代理列表已生成: {output_file}")
    
    def generate_shadowrocket(self, proxies: List[Dict]):
        """生成 ShadowRocket 格式订阅"""
        sr_lines = []
        
        for idx, proxy in enumerate(proxies):
            address = proxy.get('proxy', '') or f"{proxy.get('ip')}:{proxy.get('port')}"
            if ':' not in address:
                continue
                
            ip, port = address.split(':')
            country = proxy.get('country', 'UN')
            score = self._get_score(proxy)
            
            # ShadowRocket SOCKS5 格式
            # socks5://ip:port#备注
            name = f"{country}_{idx:03d}_S{int(score)}"
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
        
        # 简单的国家统计
        countries = {}
        for p in self.proxies:
            c = p.get('country', 'Unknown')
            countries[c] = countries.get(c, 0) + 1

        return {
            'total_proxies': len(self.proxies),
            'countries': countries,
            'files': files_info,
            'update_time': datetime.now().isoformat()
        }


def main():
    """主函数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        print("="*60)
        print("订阅链接生成器")
        print("="*60)
        
        generator = SubscriptionGenerator()
        
        if not generator.proxies:
            logger.error("❌ 没有加载到任何代理数据")
            logger.error("   请检查 subscribe/proxies.json 文件是否存在且格式正确")
            return 1
        
        # 生成所有格式 (降低分数阈值，确保包含所有有效代理)
        generator.generate_all_formats(min_score=1.0)
        
        # 显示统计信息
        info = generator.get_subscription_info()
        print(f"\n📊 订阅统计:")
        print(f"  总代理数: {info['total_proxies']}")
        print(f"\n📁 生成的文件:")
        
        if not info['files']:
            logger.warning("⚠️ 没有生成任何订阅文件")
            return 1
        
        for file_name, file_info in info['files'].items():
            print(f"  ✅ {file_name} ({file_info['size_kb']} KB)")
        
        print(f"\n✨ 完成！订阅文件已保存到 subscribe/ 目录")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"❌ 文件未找到: {e}")
        logger.error("   请确保 subscribe/proxies.json 存在")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON格式错误: {e}")
        logger.error("   请检查 subscribe/proxies.json 文件格式")
        return 1
    except Exception as e:
        logger.error(f"❌ 生成订阅文件时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())

