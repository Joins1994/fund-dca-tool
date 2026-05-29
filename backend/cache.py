#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据持久化缓存模块
用于缓存历史数据和API响应，避免重复请求
"""

import json
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional
from config import Config


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        from logger import get_logger
        self.logger = get_logger("cache")
        
        self.cache_dir = cache_dir or Config.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, key: str, prefix: str = "") -> Path:
        """
        获取缓存文件路径
        
        Args:
            key: 缓存键
            prefix: 前缀
        
        Returns:
            Path: 缓存文件路径
        """
        safe_key = "".join(c for c in key if c.isalnum() or c in "-_")
        if prefix:
            safe_key = f"{prefix}_{safe_key}"
        return self.cache_dir / f"{safe_key}.cache"
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, prefix: str = "") -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间(秒)，None表示不自动过期
            prefix: 前缀
        
        Returns:
            bool: 是否成功
        """
        try:
            cache_path = self._get_cache_path(key, prefix)
            expire_at = (datetime.now() + timedelta(seconds=ttl)) if ttl else None
            
            cache_data = {
                "value": value,
                "expire_at": expire_at.isoformat() if expire_at else None,
                "created_at": datetime.now().isoformat()
            }
            
            # 尝试用 pickle 存储，支持更多类型
            try:
                with open(cache_path, 'wb') as f:
                    pickle.dump(cache_data, f)
            except (pickle.PickleError, TypeError):
                # 如果 pickle 失败，尝试 json
                try:
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False, default=str)
                except Exception as e:
                    self.logger.error(f"JSON 序列化失败: {e}")
                    return False
            
            self.logger.debug(f"缓存已设置: {prefix}:{key}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置缓存失败 {key}: {e}")
            return False
    
    def get(self, key: str, prefix: str = "") -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
            prefix: 前缀
        
        Returns:
            Any: 缓存值，None表示未命中或已过期
        """
        try:
            cache_path = self._get_cache_path(key, prefix)
            
            if not cache_path.exists():
                return None
            
            # 先尝试用 pickle 读取
            try:
                with open(cache_path, 'rb') as f:
                    cache_data = pickle.load(f)
            except (pickle.UnpicklingError, EOFError):
                # 如果 pickle 失败，尝试 json
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                except Exception:
                    # 都失败则删除文件
                    cache_path.unlink(missing_ok=True)
                    return None
            
            # 检查是否过期
            if cache_data.get("expire_at"):
                expire_at = datetime.fromisoformat(cache_data["expire_at"])
                if datetime.now() > expire_at:
                    self.logger.debug(f"缓存已过期: {prefix}:{key}")
                    cache_path.unlink(missing_ok=True)
                    return None
            
            self.logger.debug(f"缓存命中: {prefix}:{key}")
            return cache_data.get("value")
            
        except Exception as e:
            self.logger.error(f"获取缓存失败 {key}: {e}")
            return None
    
    def delete(self, key: str, prefix: str = "") -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            prefix: 前缀
        
        Returns:
            bool: 是否成功
        """
        try:
            cache_path = self._get_cache_path(key, prefix)
            cache_path.unlink(missing_ok=True)
            self.logger.debug(f"缓存已删除: {prefix}:{key}")
            return True
        except Exception as e:
            self.logger.error(f"删除缓存失败 {key}: {e}")
            return False
    
    def clear(self, prefix: str = "") -> int:
        """
        清除指定前缀的缓存
        
        Args:
            prefix: 前缀
        
        Returns:
            int: 删除的文件数量
        """
        count = 0
        try:
            if prefix:
                pattern = f"{prefix}_*.cache"
            else:
                pattern = "*.cache"
            
            for cache_file in self.cache_dir.glob(pattern):
                cache_file.unlink(missing_ok=True)
                count += 1
            
            self.logger.info(f"已清除 {count} 个缓存文件 (prefix:{prefix})")
            
        except Exception as e:
            self.logger.error(f"清除缓存失败: {e}")
        
        return count


# 全局缓存实例
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取缓存管理器单例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def set_cache(key: str, value: Any, ttl: Optional[int] = None, prefix: str = "") -> bool:
    """设置缓存（便捷函数）"""
    return get_cache_manager().set(key, value, ttl, prefix)


def get_cache(key: str, prefix: str = "") -> Optional[Any]:
    """获取缓存（便捷函数）"""
    return get_cache_manager().get(key, prefix)


def delete_cache(key: str, prefix: str = "") -> bool:
    """删除缓存（便捷函数）"""
    return get_cache_manager().delete(key, prefix)
