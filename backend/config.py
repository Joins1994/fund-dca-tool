#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目配置管理模块
统一管理环境变量和应用配置
"""

import os
from pathlib import Path
from dotenv import load_dotenv


def get_project_root() -> Path:
    """
    获取项目根目录（以 .env 文件所在目录为根）
    
    Returns:
        Path: 项目根目录路径对象
    """
    current_dir = Path(__file__).parent
    # 向上查找 .env 文件
    for parent in [current_dir] + list(current_dir.parents):
        if (parent / ".env").exists():
            return parent
    return current_dir


class Config:
    """应用配置类"""
    
    # 项目根目录
    ROOT_DIR = get_project_root()
    
    # Flask 配置
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))
    
    # 数据库配置
    DB_PATH = ROOT_DIR / os.getenv("DB_PATH", "fund_dca.db")
    
    # 缓存配置
    CACHE_DIR = ROOT_DIR / os.getenv("CACHE_DIR", "cache")
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
    QUOTES_CACHE_TTL = int(os.getenv("QUOTES_CACHE_TTL", "60"))
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = ROOT_DIR / os.getenv("LOG_DIR", "logs")
    LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", "30"))
    
    # 备份配置
    BACKUP_DIR = ROOT_DIR / os.getenv("BACKUP_DIR", "backups")
    BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "90"))
    
    @classmethod
    def ensure_dirs(cls):
        """确保必要的目录存在"""
        dirs_to_create = [
            cls.CACHE_DIR,
            cls.LOG_DIR,
            cls.BACKUP_DIR
        ]
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)


def init_config():
    """初始化配置"""
    # 加载 .env 文件
    project_root = get_project_root()
    env_file = project_root / ".env"
    
    if env_file.exists():
        load_dotenv(env_file)
    
    # 确保目录存在
    Config.ensure_dirs()
    
    return Config


# 初始化配置
config = init_config()
