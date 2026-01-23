"""
时区处理工具模块
提供统一的时区感知时间处理功能
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


# 定义常用时区
UTC = timezone.utc
CHINA = timezone(timedelta(hours=8), 'Asia/Shanghai')


def now_utc() -> datetime:
    """
    获取当前 UTC 时间（带时区信息）
    
    Returns:
        带 UTC 时区信息的 datetime 对象
    """
    return datetime.now(UTC)


def now_china() -> datetime:
    """
    获取当前中国时间（带时区信息）
    
    Returns:
        带中国时区信息的 datetime 对象
    """
    return datetime.now(CHINA)


def to_china_time(dt: datetime) -> datetime:
    """
    将任意时区的时间转换为中国时间
    
    Args:
        dt: datetime 对象（可以是任意时区）
        
    Returns:
        转换为中国时区的 datetime 对象
    """
    if dt.tzinfo is None:
        # 如果没有时区信息，假定为 UTC
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(CHINA)


def to_utc(dt: datetime) -> datetime:
    """
    将任意时区的时间转换为 UTC
    
    Args:
        dt: datetime 对象（可以是任意时区）
        
    Returns:
        转换为 UTC 时区的 datetime 对象
    """
    if dt.tzinfo is None:
        # 如果没有时区信息，假定为本地时区
        dt = dt.replace(tzinfo=CHINA)
    return dt.astimezone(UTC)


def format_datetime(dt: datetime, tz: Optional[timezone] = None, 
                    fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    格式化时间，可选择时区转换
    
    Args:
        dt: datetime 对象
        tz: 目标时区（None 表示使用原时区）
        fmt: 时间格式字符串
        
    Returns:
        格式化后的时间字符串
    """
    if tz:
        dt = dt.astimezone(tz)
    return dt.strftime(fmt)


def format_china_time(dt: datetime, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    格式化为中国时间字符串
    
    Args:
        dt: datetime 对象
        fmt: 时间格式字符串
        
    Returns:
        中国时区的格式化时间字符串
    """
    china_dt = to_china_time(dt)
    return china_dt.strftime(fmt)


def parse_iso_datetime(iso_string: str) -> datetime:
    """
    解析 ISO 格式的时间字符串
    
    Args:
        iso_string: ISO 8601 格式的时间字符串
        
    Returns:
        datetime 对象
    """
    try:
        return datetime.fromisoformat(iso_string)
    except ValueError:
        # 兼容不带时区的 ISO 格式
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt


def get_timestamp_utc() -> str:
    """
    获取当前 UTC 时间戳（ISO 格式）
    
    Returns:
        ISO 格式的 UTC 时间字符串
    """
    return now_utc().isoformat()


def get_timestamp_china() -> str:
    """
    获取当前中国时间戳（ISO 格式）
    
    Returns:
        ISO 格式的中国时间字符串
    """
    return now_china().isoformat()


def get_display_time() -> str:
    """
    获取用户友好的显示时间（中国时区）
    
    Returns:
        格式化的中国时间字符串
    """
    return format_china_time(now_utc(), '%Y-%m-%d %H:%M:%S')
