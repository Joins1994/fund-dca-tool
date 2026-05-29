#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理模块
使用 Python 标准库 logging，支持按日期轮转和多服务独立日志
"""

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime
import glob
import re


def get_logger(prefix: str = "", level: str = "INFO", log_dir: Path = None, retention_days: int = 30) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        prefix: 日志前缀，用于区分不同服务/模块
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志文件存储目录
        retention_days: 日志保留天数
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    from config import Config
    
    # 使用默认配置
    if log_dir is None:
        log_dir = Config.LOG_DIR
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # 构造 logger 名称
    logger_name = prefix if prefix else "app"
    logger = logging.getLogger(logger_name)
    
    # 避免重复配置
    if logger.handlers:
        return logger
    
    logger.setLevel(log_level)
    logger.propagate = False  # 不向上传递日志到 root
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台输出 handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)
    
    # 文件输出 handler (按天轮转)
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 构造日志文件名
        if prefix:
            filename_pattern = f"{prefix}_%Y-%m-%d.log"
        else:
            filename_pattern = "%Y-%m-%d.log"
        
        # 使用当前日期的文件
        current_date = datetime.now().strftime('%Y-%m-%d')
        if prefix:
            log_file = log_dir / f"{prefix}_{current_date}.log"
        else:
            log_file = log_dir / f"{current_date}.log"
        
        file_handler = TimedRotatingFileHandler(
            log_file,
            when='midnight',  # 每天午夜轮转
            interval=1,
            backupCount=0,  # 不限制数量，我们用 retention_days 管理
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)
    
    # 清理旧日志 (只清理该 prefix 对应的日志)
    _cleanup_old_logs(log_dir, prefix, retention_days)
    
    return logger


def _cleanup_old_logs(log_dir: Path, prefix: str, retention_days: int):
    """
    清理旧的日志文件
    
    Args:
        log_dir: 日志目录
        prefix: 日志前缀
        retention_days: 保留天数
    """
    if retention_days <= 0:
        return
    
    try:
        # 构造匹配模式
        if prefix:
            pattern = f"{prefix}_*.log"
        else:
            pattern = "*.log"
        
        log_files = glob.glob(str(log_dir / pattern))
        
        cutoff_date = datetime.now()
        date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})')
        
        for log_file in log_files:
            match = date_pattern.search(log_file)
            if not match:
                continue
            
            try:
                file_date = datetime.strptime(match.group(1), '%Y-%m-%d')
                days_diff = (cutoff_date - file_date).days
                
                if days_diff > retention_days:
                    Path(log_file).unlink(missing_ok=True)
            except (ValueError, OSError):
                continue
                
    except Exception:
        pass  # 清理失败不影响应用
