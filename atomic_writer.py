"""
原子文件写入工具模块
提供安全的文件写入功能，确保写入过程的原子性
"""

import os
import tempfile
import logging
from typing import Union
from pathlib import Path

logger = logging.getLogger(__name__)


def atomic_write(
    file_path: Union[str, Path],
    content: Union[str, bytes],
    encoding: str = 'utf-8',
    mode: str = 'w'
) -> bool:
    """
    原子性写入文件，防止写入中断导致文件损坏
    
    策略：
    1. 写入临时文件（优先同目录，只读时使用系统临时目录）
    2. 校验文件大小 > 0
    3. 原子性重命名替换目标文件
    
    兼容性：
    - 支持只读文件系统 (Koyeb, Hugging Face Spaces)
    - 自动检测目录写权限并降级到 /tmp
    
    Args:
        file_path: 目标文件路径
        content: 要写入的内容（字符串或字节）
        encoding: 字符编码（默认utf-8，仅用于文本模式）
        mode: 写入模式 'w'文本 或 'wb'二进制
        
    Returns:
        bool: 写入成功返回True，失败返回False
        
    使用示例:
        # 文本写入
        atomic_write('output.txt', 'Hello World')
        
        # 二进制写入
        atomic_write('output.bin', b'binary data', mode='wb')
    """
    import tempfile
    
    try:
        file_path = Path(file_path)
        
        # 1. 确保目标目录存在
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            logger.warning(f"无法创建目录 {file_path.parent}: {e}")
        
        # 2. 检测目标目录是否可写
        target_dir = file_path.parent
        is_writable = os.access(target_dir, os.W_OK) if target_dir.exists() else False
        
        # 3. 选择临时文件位置
        if is_writable:
            # 优先使用同目录（确保原子性）
            temp_dir = target_dir
        else:
            # 降级到系统临时目录（容器化环境兼容）
            temp_dir = None  # NamedTemporaryFile 会自动使用系统临时目录
            logger.warning(f"目标目录只读，使用系统临时目录: {file_path.parent}")
        
        # 4. 创建临时文件并写入
        with tempfile.NamedTemporaryFile(
            mode=mode if 'b' in mode else 'w',
            encoding=encoding if 'b' not in mode else None,
            delete=False,
            dir=temp_dir,
            prefix=f".{file_path.stem}_",
            suffix=".tmp"
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(content)
        
        # 5. 校验文件大小
        file_size = temp_path.stat().st_size
        if file_size == 0:
            temp_path.unlink()
            logger.error(f"写入失败: {file_path} - 文件大小为0")
            return False
        
        # 6. 原子性重命名（os.replace 跨平台原子操作）
        try:
            os.replace(temp_path, file_path)
            logger.debug(f"原子写入成功: {file_path} ({file_size} bytes)")
            return True
        except OSError as e:
            # 如果跨文件系统，手动复制
            logger.warning(f"跨文件系统写入，使用复制模式: {e}")
            import shutil
            shutil.move(str(temp_path), str(file_path))
            logger.debug(f"原子写入成功 (复制模式): {file_path} ({file_size} bytes)")
            return True
        
    except PermissionError as e:
        logger.error(f"权限不足，无法写入 {file_path}: {e}")
        logger.warning(f"💡 提示: 确保目标目录在容器化环境的可写路径 (如 /tmp, /workspace, /data)")
        return False
    except Exception as e:
        logger.error(f"原子写入失败 {file_path}: {e}")
        
        # 清理临时文件
        try:
            if 'temp_path' in locals() and temp_path.exists():
                temp_path.unlink()
        except:
            pass
        
        return False


def safe_write_lines(file_path: Union[str, Path], lines: list, encoding: str = 'utf-8') -> bool:
    """
    安全写入多行文本（每行自动添加换行符）
    
    Args:
        file_path: 目标文件路径
        lines: 行列表
        encoding: 字符编码
        
    Returns:
        bool: 写入成功返回True
    """
    content = '\n'.join(lines) + '\n' if lines else ''
    return atomic_write(file_path, content, encoding=encoding, mode='w')


def safe_write_json(file_path: Union[str, Path], data: dict, encoding: str = 'utf-8', indent: int = 2) -> bool:
    """
    安全写入JSON文件
    
    Args:
        file_path: 目标文件路径
        data: 要序列化的字典
        encoding: 字符编码
        indent: 缩进空格数
        
    Returns:
        bool: 写入成功返回True
    """
    import json
    try:
        content = json.dumps(data, ensure_ascii=False, indent=indent)
        return atomic_write(file_path, content, encoding=encoding, mode='w')
    except Exception as e:
        logger.error(f"JSON序列化失败: {e}")
        return False


def ensure_directory(directory: Union[str, Path]) -> bool:
    """
    确保目录存在，不存在则创建
    
    Args:
        directory: 目录路径
        
    Returns:
        bool: 成功返回True
    """
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"创建目录失败 {directory}: {e}")
        return False
