"""
代理数据库管理模块
提供代理历史记录存储、统计分析和智能查询功能
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Set
import logging
from contextlib import contextmanager


class ProxyDatabase:
    """代理数据库管理器"""
    
    def __init__(self, db_path: str = "proxies.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 代理记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS proxies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proxy_address TEXT NOT NULL,
                    ip TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    country TEXT,
                    country_code TEXT,
                    city TEXT,
                    isp TEXT,
                    is_mobile BOOLEAN DEFAULT 0,
                    is_proxy BOOLEAN DEFAULT 0,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(proxy_address)
                )
            """)
            
            # 验证历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS validation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proxy_id INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_valid BOOLEAN NOT NULL,
                    response_time REAL,
                    test_url TEXT,
                    error_message TEXT,
                    score REAL DEFAULT 0,
                    FOREIGN KEY (proxy_id) REFERENCES proxies(id)
                )
            """)
            
            # 代理源表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS proxy_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_url TEXT UNIQUE NOT NULL,
                    source_type TEXT DEFAULT 'http',
                    last_check TIMESTAMP,
                    success_count INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0,
                    total_proxies_found INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # 代理黑名单表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS proxy_blacklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proxy_address TEXT UNIQUE NOT NULL,
                    fail_count INTEGER DEFAULT 1,
                    first_failed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_failed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT,
                    auto_added BOOLEAN DEFAULT 1
                )
            """)
            
            # 创建索引优化查询
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_proxy_address ON proxies(proxy_address)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_last_seen ON proxies(last_seen)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_validation_proxy_id ON validation_history(proxy_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_validation_timestamp ON validation_history(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_blacklist_address ON proxy_blacklist(proxy_address)")
            
            self.logger.info("数据库初始化完成")
    
    # ========== 黑名单管理 ==========
    
    def add_to_blacklist(self, proxy_address: str, reason: str = "连续失败", auto_added: bool = True):
        """
        将代理添加到黑名单
        
        Args:
            proxy_address: 代理地址
            reason: 加入黑名单的原因
            auto_added: 是否自动添加
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO proxy_blacklist (proxy_address, reason, auto_added)
                VALUES (?, ?, ?)
                ON CONFLICT(proxy_address) DO UPDATE SET
                    fail_count = fail_count + 1,
                    last_failed = CURRENT_TIMESTAMP,
                    reason = ?
            """, (proxy_address, reason, auto_added, reason))
            
            # 改为debug级别，避免日志刷屏
            self.logger.debug(f"代理 {proxy_address} 已加入黑名单: {reason}")
    
    def is_blacklisted(self, proxy_address: str) -> bool:
        """检查代理是否在黑名单中"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM proxy_blacklist WHERE proxy_address = ?", (proxy_address,))
            return cursor.fetchone() is not None
    
    def get_blacklisted_proxies(self) -> Set[str]:
        """获取所有黑名单代理"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT proxy_address FROM proxy_blacklist")
            return {row['proxy_address'] for row in cursor.fetchall()}
    
    def remove_from_blacklist(self, proxy_address: str):
        """从黑名单中移除代理"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM proxy_blacklist WHERE proxy_address = ?", (proxy_address,))
            if cursor.rowcount > 0:
                self.logger.info(f"代理 {proxy_address} 已从黑名单移除")
    
    def auto_blacklist_failing_proxies(self, fail_threshold: int = 5, days: int = 7):
        """
        自动将持续失败的代理加入黑名单
        
        Args:
            fail_threshold: 失败次数阈值
            days: 检查最近几天的记录
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 找出连续失败的代理
            cursor.execute("""
                SELECT 
                    p.proxy_address,
                    COUNT(*) as total_checks,
                    SUM(CASE WHEN vh.is_valid = 0 THEN 1 ELSE 0 END) as fail_count
                FROM proxies p
                INNER JOIN validation_history vh ON p.id = vh.proxy_id
                WHERE vh.timestamp >= ?
                GROUP BY p.proxy_address
                HAVING fail_count >= ? AND fail_count = total_checks
            """, (cutoff_date, fail_threshold))
            
            blacklisted_count = 0
            for row in cursor.fetchall():
                proxy_address = row['proxy_address']
                if not self.is_blacklisted(proxy_address):
                    self.add_to_blacklist(
                        proxy_address,
                        f"最近{days}天连续失败{row['fail_count']}次",
                        auto_added=True
                    )
                    blacklisted_count += 1
            
            if blacklisted_count > 0:
                self.logger.info(f"自动将 {blacklisted_count} 个持续失败的代理加入黑名单")
            
            return blacklisted_count
    
    def get_blacklist_stats(self) -> Dict:
        """获取黑名单统计信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM proxy_blacklist")
            total = cursor.fetchone()['count']
            
            cursor.execute("""
                SELECT COUNT(*) as count FROM proxy_blacklist 
                WHERE auto_added = 1
            """)
            auto_added = cursor.fetchone()['count']
            
            cursor.execute("""
                SELECT proxy_address, fail_count, reason, last_failed
                FROM proxy_blacklist
                ORDER BY fail_count DESC
                LIMIT 10
            """)
            top_failures = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_blacklisted': total,
                'auto_added': auto_added,
                'manual_added': total - auto_added,
                'top_failures': top_failures
            }
    
    # ========== 原有方法 ==========
    
    def save_proxy(self, proxy_data: Dict) -> int:
        """
        保存或更新代理信息
        
        Args:
            proxy_data: 包含代理信息的字典
            
        Returns:
            代理ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            proxy_address = proxy_data.get('proxy')
            if not proxy_address or ':' not in proxy_address:
                raise ValueError(f"无效的代理地址: {proxy_address}")
            
            ip, port = proxy_address.split(':')
            
            # 检查代理是否已存在
            cursor.execute("SELECT id FROM proxies WHERE proxy_address = ?", (proxy_address,))
            row = cursor.fetchone()
            
            if row:
                # 更新现有代理
                proxy_id = row['id']
                cursor.execute("""
                    UPDATE proxies 
                    SET last_seen = CURRENT_TIMESTAMP,
                        country = COALESCE(?, country),
                        country_code = COALESCE(?, country_code),
                        city = COALESCE(?, city),
                        isp = COALESCE(?, isp),
                        is_mobile = COALESCE(?, is_mobile),
                        is_proxy = COALESCE(?, is_proxy)
                    WHERE id = ?
                """, (
                    proxy_data.get('country'),
                    proxy_data.get('country_code'),
                    proxy_data.get('city'),
                    proxy_data.get('isp'),
                    proxy_data.get('is_mobile'),
                    proxy_data.get('is_proxy'),
                    proxy_id
                ))
            else:
                # 插入新代理
                cursor.execute("""
                    INSERT INTO proxies (
                        proxy_address, ip, port, country, country_code, 
                        city, isp, is_mobile, is_proxy
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    proxy_address,
                    ip,
                    int(port),
                    proxy_data.get('country'),
                    proxy_data.get('country_code'),
                    proxy_data.get('city'),
                    proxy_data.get('isp'),
                    proxy_data.get('is_mobile', False),
                    proxy_data.get('is_proxy', False)
                ))
                proxy_id = cursor.lastrowid
            
            return proxy_id
    
    def save_validation_result(self, proxy_address: str, validation_data: Dict):
        """保存验证结果"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取代理ID
            cursor.execute("SELECT id FROM proxies WHERE proxy_address = ?", (proxy_address,))
            row = cursor.fetchone()
            
            if not row:
                self.logger.warning(f"代理 {proxy_address} 不存在于数据库中")
                return
            
            proxy_id = row['id']
            
            cursor.execute("""
                INSERT INTO validation_history (
                    proxy_id, is_valid, response_time, test_url, error_message, score
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                proxy_id,
                validation_data.get('is_valid', False),
                validation_data.get('response_time'),
                validation_data.get('test_url'),
                validation_data.get('error'),
                validation_data.get('score', 0)
            ))
    
    def get_proxy_stats(self, proxy_address: str) -> Optional[Dict]:
        """获取代理的统计信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    p.*,
                    COUNT(vh.id) as total_checks,
                    SUM(CASE WHEN vh.is_valid THEN 1 ELSE 0 END) as success_count,
                    AVG(CASE WHEN vh.is_valid THEN vh.response_time END) as avg_response_time,
                    MAX(vh.timestamp) as last_check,
                    AVG(vh.score) as avg_score
                FROM proxies p
                LEFT JOIN validation_history vh ON p.id = vh.proxy_id
                WHERE p.proxy_address = ?
                GROUP BY p.id
            """, (proxy_address,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            stats = dict(row)
            if stats['total_checks'] > 0:
                stats['success_rate'] = stats['success_count'] / stats['total_checks']
            else:
                stats['success_rate'] = 0
            
            return stats
    
    def get_best_proxies(self, limit: int = 50, min_checks: int = 3, 
                         min_success_rate: float = 0.5) -> List[Dict]:
        """
        获取最佳代理列表
        
        Args:
            limit: 返回数量
            min_checks: 最小检查次数
            min_success_rate: 最小成功率
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    p.proxy_address,
                    p.country,
                    p.country_code,
                    p.city,
                    p.isp,
                    p.is_mobile,
                    p.first_seen,
                    p.last_seen,
                    COUNT(vh.id) as total_checks,
                    SUM(CASE WHEN vh.is_valid THEN 1 ELSE 0 END) as success_count,
                    AVG(CASE WHEN vh.is_valid THEN vh.response_time END) as avg_response_time,
                    AVG(vh.score) as avg_score,
                    MAX(vh.timestamp) as last_check
                FROM proxies p
                INNER JOIN validation_history vh ON p.id = vh.proxy_id
                LEFT JOIN proxy_blacklist bl ON p.proxy_address = bl.proxy_address
                WHERE bl.id IS NULL
                GROUP BY p.id
                HAVING 
                    total_checks >= ? 
                    AND (success_count * 1.0 / total_checks) >= ?
                ORDER BY avg_score DESC, avg_response_time ASC
                LIMIT ?
            """, (min_checks, min_success_rate, limit))
            
            results = []
            for row in cursor.fetchall():
                proxy = dict(row)
                proxy['success_rate'] = proxy['success_count'] / proxy['total_checks']
                results.append(proxy)
            
            return results
    
    def get_all_active_proxies(self, hours: int = 24) -> List[str]:
        """获取最近活跃的所有代理地址"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute("""
                SELECT proxy_address 
                FROM proxies 
                WHERE last_seen >= ?
                ORDER BY last_seen DESC
            """, (cutoff_time,))
            
            return [row['proxy_address'] for row in cursor.fetchall()]
    
    def cleanup_old_records(self, days: int = 30):
        """清理旧记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 删除旧的验证历史
            cursor.execute("""
                DELETE FROM validation_history 
                WHERE timestamp < ?
            """, (cutoff_date,))
            deleted_validations = cursor.rowcount
            
            # 删除长期未见的代理
            cursor.execute("""
                DELETE FROM proxies 
                WHERE last_seen < ? 
                AND id NOT IN (
                    SELECT DISTINCT proxy_id 
                    FROM validation_history
                )
            """, (cutoff_date,))
            deleted_proxies = cursor.rowcount
            
            # 清理旧的黑名单记录
            cursor.execute("""
                DELETE FROM proxy_blacklist
                WHERE last_failed < ?
            """, (cutoff_date,))
            deleted_blacklist = cursor.rowcount
            
            self.logger.info(
                f"清理完成: 删除 {deleted_validations} 条验证记录, "
                f"{deleted_proxies} 个代理, {deleted_blacklist} 条黑名单记录"
            )
        
        # VACUUM 必须在事务外执行
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("VACUUM")
            conn.close()
            self.logger.info("数据库压缩完成")
        except Exception as e:
            self.logger.warning(f"数据库压缩失败: {e}")
        
        return deleted_validations, deleted_proxies
    
    def get_database_stats(self) -> Dict:
        """获取数据库统计信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # 总代理数
            cursor.execute("SELECT COUNT(*) as count FROM proxies")
            stats['total_proxies'] = cursor.fetchone()['count']
            
            # 24小时内活跃代理数
            cursor.execute("""
                SELECT COUNT(*) as count FROM proxies 
                WHERE last_seen >= datetime('now', '-24 hours')
            """)
            stats['active_proxies_24h'] = cursor.fetchone()['count']
            
            # 总验证次数
            cursor.execute("SELECT COUNT(*) as count FROM validation_history")
            stats['total_validations'] = cursor.fetchone()['count']
            
            # 最近24小时验证成功率
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_valid THEN 1 ELSE 0 END) as valid
                FROM validation_history
                WHERE timestamp >= datetime('now', '-24 hours')
            """)
            row = cursor.fetchone()
            if row['total'] > 0:
                stats['success_rate_24h'] = row['valid'] / row['total']
            else:
                stats['success_rate_24h'] = 0
            
            # 黑名单数量
            cursor.execute("SELECT COUNT(*) as count FROM proxy_blacklist")
            stats['blacklisted_count'] = cursor.fetchone()['count']
            
            # 24小时平均响应时间
            cursor.execute("""
                SELECT AVG(response_time) as avg_time
                FROM validation_history
                WHERE timestamp >= datetime('now', '-24 hours')
                    AND is_valid = 1
                    AND response_time IS NOT NULL
            """)
            row = cursor.fetchone()
            stats['avg_response_time_24h'] = row['avg_time'] if row['avg_time'] else 0
            
            # 国家分布
            cursor.execute("""
                SELECT country, COUNT(*) as count
                FROM proxies
                WHERE country IS NOT NULL
                GROUP BY country
                ORDER BY count DESC
                LIMIT 10
            """)
            stats['top_countries'] = [
                {'country': row['country'], 'count': row['count']}
                for row in cursor.fetchall()
            ]
            
            # 简化的国家分布字典（用于兼容性）
            stats['country_distribution'] = {
                row['country']: row['count']
                for row in stats['top_countries']
            }
            
            return stats
    
    def update_source_stats(self, source_url: str, success: bool, proxies_found: int = 0):
        """更新代理源统计"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO proxy_sources (source_url, last_check, success_count, fail_count, total_proxies_found)
                VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?)
                ON CONFLICT(source_url) DO UPDATE SET
                    last_check = CURRENT_TIMESTAMP,
                    success_count = success_count + ?,
                    fail_count = fail_count + ?,
                    total_proxies_found = total_proxies_found + ?
            """, (
                source_url,
                1 if success else 0,
                0 if success else 1,
                proxies_found,
                1 if success else 0,
                0 if success else 1,
                proxies_found
            ))
    
    def get_source_health(self) -> List[Dict]:
        """获取代理源健康状态"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    source_url,
                    source_type,
                    last_check,
                    success_count,
                    fail_count,
                    total_proxies_found,
                    is_active,
                    CASE 
                        WHEN (success_count + fail_count) > 0 
                        THEN (success_count * 1.0 / (success_count + fail_count))
                        ELSE 0 
                    END as success_rate
                FROM proxy_sources
                ORDER BY success_rate DESC, total_proxies_found DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
