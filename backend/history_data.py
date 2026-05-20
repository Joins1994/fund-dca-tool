#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指数历史数据获取模块
支持获取各指数创立以来的历史数据
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta

# 指数创立日期
INDEX_START_DATES = {
    'sh000300': '2005-04-08',  # 沪深300
    'sh000016': '2004-01-02',  # 上证50
    'sh000905': '2007-01-15',  # 中证500
    'sh000688': '2020-01-23',  # 科创50
    'sz399006': '2010-06-01',  # 创业板指
    'sh000852': '2014-10-17'   # 中证1000
}

# 指数名称映射
INDEX_NAMES = {
    'sh000300': '沪深300',
    'sh000016': '上证50',
    'sh000905': '中证500',
    'sh000688': '科创50',
    'sz399006': '创业板指',
    'sh000852': '中证1000'
}


def fetch_index_history_from_sina(symbol, start_date=None, end_date=None):
    """
    从新浪财经获取指数历史K线数据
    
    参数:
        symbol: 指数代码，如 sh000300
        start_date: 开始日期，格式 YYYY-MM-DD
        end_date: 结束日期，格式 YYYY-MM-DD
    
    返回:
        DataFrame 包含日期、开盘、收盘、最高、最低、成交量
    """
    try:
        # 新浪财经K线数据API
        # scale: 240表示日线, 60表示60分钟线
        # datalen: 获取数据条数，最多1023条
        
        url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
        
        all_data = []
        
        # 由于新浪API限制，每次最多获取1023条数据
        # 需要分批获取
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        if not start_date:
            start_date = INDEX_START_DATES.get(symbol, '2010-01-01')
        
        # 计算需要获取的数据批次
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        days = (end - start).days
        
        # 每次获取1000条数据（留一些余量）
        batch_size = 1000
        batches = (days // batch_size) + 1
        
        for i in range(batches):
            params = {
                'symbol': symbol,
                'scale': 240,  # 日线
                'ma': 'no',
                'datalen': batch_size
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://finance.sina.com.cn'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            
            # 解析返回的JSONP格式数据
            text = response.text
            if text and text != 'null':
                try:
                    # 新浪返回的是JSON格式
                    data = json.loads(text)
                    if data and isinstance(data, list):
                        all_data.extend(data)
                except:
                    # 如果是JSONP格式，需要去除回调函数
                    if '(' in text and ')' in text:
                        text = text[text.find('(')+1:text.rfind(')')]
                        data = json.loads(text)
                        if data and isinstance(data, list):
                            all_data.extend(data)
            
            # 避免请求过快
            import time
            time.sleep(0.5)
        
        if all_data:
            df = pd.DataFrame(all_data)
            # 转换日期格式
            if 'day' in df.columns:
                df['date'] = pd.to_datetime(df['day'])
            df = df.sort_values('date')
            return df
        
        return None
        
    except Exception as e:
        print(f"获取历史数据失败 {symbol}: {e}")
        return None


def fetch_index_history_from_eastmoney(symbol, start_date=None, end_date=None):
    """
    从东方财富获取指数历史数据
    备用数据源
    """
    try:
        # 东方财富API
        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get"
        
        # 转换代码格式
        if symbol.startswith('sh'):
            secid = f"1.{symbol[2:]}"
        elif symbol.startswith('sz'):
            secid = f"0.{symbol[2:]}"
        else:
            secid = symbol
        
        if not start_date:
            start_date = INDEX_START_DATES.get(symbol, '20100101').replace('-', '')
        else:
            start_date = start_date.replace('-', '')
        
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        else:
            end_date = end_date.replace('-', '')
        
        params = {
            'secid': secid,
            'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
            'fields1': 'f1,f2,f3,f4,f5,f6',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
            'klt': 101,  # 日线
            'fqt': 0,    # 不复权
            'beg': start_date,
            'end': end_date,
            'smplmt': 100000,  # 获取所有数据
            '_': int(datetime.now().timestamp() * 1000)
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        data = response.json()
        
        if data.get('data') and data['data'].get('klines'):
            klines = data['data']['klines']
            
            # 解析K线数据
            # 格式: 日期,开盘,收盘,最低,最高,成交量,成交额,振幅,涨跌幅,涨跌额,换手率
            parsed_data = []
            for line in klines:
                parts = line.split(',')
                if len(parts) >= 6:
                    parsed_data.append({
                        'date': parts[0],
                        'open': float(parts[1]),
                        'close': float(parts[2]),
                        'low': float(parts[3]),
                        'high': float(parts[4]),
                        'volume': float(parts[5]),
                        'amount': float(parts[6]) if len(parts) > 6 else 0
                    })
            
            df = pd.DataFrame(parsed_data)
            df['date'] = pd.to_datetime(df['date'])
            return df
        
        return None
        
    except Exception as e:
        print(f"东方财富数据获取失败 {symbol}: {e}")
        return None


def generate_mock_history(symbol, days=3650):
    """
    生成模拟历史数据（当API失败时使用）
    """
    import numpy as np
    
    # 获取指数起始日期
    start_date_str = INDEX_START_DATES.get(symbol, '2010-01-01')
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    
    # 生成日期序列（只生成交易日，简化处理）
    dates = []
    current = start_date
    end_date = datetime.now()
    
    while current <= end_date:
        # 跳过周末（简化处理）
        if current.weekday() < 5:
            dates.append(current)
        current += timedelta(days=1)
    
    # 生成价格数据
    np.random.seed(hash(symbol) % 2**32)
    
    # 基础价格
    base_prices = {
        'sh000300': 3500,
        'sh000016': 2500,
        'sh000905': 6000,
        'sh000688': 1000,
        'sz399006': 2000,
        'sh000852': 7000
    }
    
    base_price = base_prices.get(symbol, 3000)
    
    # 生成随机 walk
    returns = np.random.normal(0.0002, 0.015, len(dates))
    prices = base_price * np.exp(np.cumsum(returns))
    
    # 生成OHLC数据
    data = []
    for i, date in enumerate(dates):
        price = prices[i]
        volatility = price * 0.01
        
        open_price = price + np.random.normal(0, volatility * 0.3)
        close_price = price
        high_price = max(open_price, close_price) + np.random.uniform(0, volatility)
        low_price = min(open_price, close_price) - np.random.uniform(0, volatility)
        
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'open': round(open_price, 2),
            'close': round(close_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'volume': int(np.random.uniform(100000000, 500000000)),
            'amount': int(np.random.uniform(1000000000, 5000000000))
        })
    
    return pd.DataFrame(data)


def get_index_history(symbol, use_mock=False):
    """
    获取指数历史数据的主函数
    
    参数:
        symbol: 指数代码
        use_mock: 是否使用模拟数据
    
    返回:
        DataFrame 或 None
    """
    if use_mock:
        return generate_mock_history(symbol)
    
    # 先尝试东方财富（数据更完整）
    df = fetch_index_history_from_eastmoney(symbol)
    
    if df is not None and len(df) > 0:
        print(f"成功从东方财富获取 {symbol} 历史数据，共 {len(df)} 条")
        return df
    
    # 备用：新浪
    df = fetch_index_history_from_sina(symbol)
    
    if df is not None and len(df) > 0:
        print(f"成功从新浪获取 {symbol} 历史数据，共 {len(df)} 条")
        return df
    
    # 如果都失败，使用模拟数据
    print(f"使用模拟数据 {symbol}")
    return generate_mock_history(symbol)


def get_all_indices_history():
    """
    获取所有指数的历史数据
    
    返回:
        dict: {symbol: DataFrame}
    """
    result = {}
    
    for symbol in INDEX_NAMES.keys():
        print(f"正在获取 {INDEX_NAMES[symbol]} ({symbol}) 历史数据...")
        df = get_index_history(symbol)
        if df is not None:
            result[symbol] = df
    
    return result


def calculate_pe_from_price(df, symbol):
    """
    根据价格和估值数据估算历史PE
    （简化处理，实际PE需要成分股数据计算）
    """
    # PE历史范围
    pe_ranges = {
        'sh000300': {'min': 10, 'max': 18, 'avg': 13.5},
        'sh000016': {'min': 8, 'max': 15, 'avg': 11},
        'sh000905': {'min': 15, 'max': 35, 'avg': 25},
        'sh000688': {'min': 35, 'max': 85, 'avg': 60},
        'sz399006': {'min': 25, 'max': 60, 'avg': 42},
        'sh000852': {'min': 20, 'max': 50, 'avg': 35}
    }
    
    pe_range = pe_ranges.get(symbol, {'min': 10, 'max': 30, 'avg': 20})
    
    # 根据价格相对于历史均值的位置估算PE
    avg_price = df['close'].mean()
    
    df['pe'] = df['close'].apply(
        lambda x: pe_range['avg'] + (x - avg_price) / avg_price * (pe_range['max'] - pe_range['min']) / 4
    )
    
    # 限制PE范围
    df['pe'] = df['pe'].clip(pe_range['min'], pe_range['max'])
    df['pe'] = df['pe'].round(2)
    
    # 计算PE分位
    df['pe_percentile'] = df['pe'].rank(pct=True) * 100
    df['pe_percentile'] = df['pe_percentile'].round(1)
    
    return df


if __name__ == '__main__':
    # 测试
    symbol = 'sh000300'
    df = get_index_history(symbol, use_mock=True)
    
    if df is not None:
        print(f"\n{INDEX_NAMES[symbol]} 历史数据:")
        print(f"数据条数: {len(df)}")
        print(f"日期范围: {df['date'].min()} 至 {df['date'].max()}")
        print("\n前5条数据:")
        print(df.head())
        print("\n后5条数据:")
        print(df.tail())
