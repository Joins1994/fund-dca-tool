"""
本地SQLite数据库模块
用于存储定投记录、用户设置等数据
"""

import sqlite3
import os
import json
from datetime import datetime

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'fund_dca.db')

def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """初始化数据库表"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 定投记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS investment_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            index_code TEXT NOT NULL,
            index_name TEXT NOT NULL,
            amount REAL NOT NULL,
            invest_date DATE NOT NULL,
            buy_price REAL DEFAULT 0,
            buy_index_point REAL DEFAULT 0,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 为已有表添加新字段（如果不存在）
    try:
        cursor.execute("ALTER TABLE investment_records ADD COLUMN buy_price REAL DEFAULT 0")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE investment_records ADD COLUMN buy_index_point REAL DEFAULT 0")
    except:
        pass
    
    # 用户设置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 止盈止损设置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stop_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            index_code TEXT NOT NULL,
            stop_profit REAL DEFAULT 15.0,
            stop_loss REAL DEFAULT -10.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 估值提醒设置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alert_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pe_threshold INTEGER DEFAULT 30,
            invest_day INTEGER DEFAULT 1,
            enabled INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")

# ========== 定投记录操作 ==========

def add_record(index_code, index_name, amount, invest_date, note='', buy_price=0, buy_index_point=0):
    """添加定投记录"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO investment_records (index_code, index_name, amount, invest_date, note, buy_price, buy_index_point)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (index_code, index_name, amount, invest_date, note, buy_price, buy_index_point))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return record_id

def get_records():
    """获取所有定投记录"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM investment_records ORDER BY invest_date DESC
    ''')
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return records

def delete_record(record_id):
    """删除定投记录"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM investment_records WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()
    return True

def update_record(record_id, **kwargs):
    """更新定投记录"""
    conn = get_connection()
    cursor = conn.cursor()
    
    allowed_fields = ['index_code', 'index_name', 'amount', 'invest_date', 'note']
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    
    if updates:
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [record_id]
        cursor.execute(f'''
            UPDATE investment_records 
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', values)
        conn.commit()
    
    conn.close()
    return True

def get_stats():
    """获取定投统计信息"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_times,
            COALESCE(SUM(amount), 0) as total_amount,
            COALESCE(AVG(amount), 0) as avg_amount,
            MAX(invest_date) as last_date
        FROM investment_records
    ''')
    row = cursor.fetchone()
    conn.close()
    
    return {
        'total_times': row['total_times'],
        'total_amount': row['total_amount'],
        'avg_amount': row['avg_amount'],
        'last_date': row['last_date']
    }

# ========== 设置操作 ==========

def set_setting(key, value):
    """保存设置"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_settings (setting_key, setting_value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    ''', (key, json.dumps(value) if isinstance(value, (dict, list)) else str(value)))
    conn.commit()
    conn.close()
    return True

def get_setting(key, default=None):
    """获取设置"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT setting_value FROM user_settings WHERE setting_key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        try:
            return json.loads(row['setting_value'])
        except:
            return row['setting_value']
    return default

# ========== 止盈止损设置 ==========

def save_stop_settings(index_code, stop_profit, stop_loss):
    """保存止盈止损设置"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO stop_settings (index_code, stop_profit, stop_loss, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ''', (index_code, stop_profit, stop_loss))
    conn.commit()
    conn.close()
    return True

def get_stop_settings(index_code):
    """获取止盈止损设置"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM stop_settings WHERE index_code = ?
    ''', (index_code,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_all_stop_settings():
    """获取所有止盈止损设置"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM stop_settings')
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return records

# ========== 估值提醒设置 ==========

def save_alert_settings(pe_threshold, invest_day, enabled=1):
    """保存估值提醒设置"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO alert_settings (id, pe_threshold, invest_day, enabled, updated_at)
        VALUES (1, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (pe_threshold, invest_day, enabled))
    conn.commit()
    conn.close()
    return True

def get_alert_settings():
    """获取估值提醒设置"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM alert_settings WHERE id = 1')
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return {
        'pe_threshold': 30,
        'invest_day': 1,
        'enabled': 1
    }

# 初始化数据库
if __name__ == '__main__':
    init_database()
    print("数据库初始化完成！")
