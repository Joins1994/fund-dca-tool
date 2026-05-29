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
    # A股指数
    'sh000300': '2005-04-08',  # 沪深300
    'sh000016': '2004-01-02',  # 上证50
    'sh000905': '2007-01-15',  # 中证500
    'sh000688': '2020-01-23',  # 科创50
    'sz399006': '2010-06-01',  # 创业板指
    'sh000852': '2014-10-17',  # 中证1000
    # 海外指数 (用于Yahoo Finance)
    'IXIC': '1971-02-05',      # 纳斯达克综合指数
    'SPX': '1950-01-03',       # 标普500
    'FTSE': '1984-01-03',      # 富时100
    'DAX': '1987-11-30',       # 德国DAX
    'N225': '1984-01-04',      # 日经225
    'HSI': '1967-11-24'        # 恒生指数
}

# 指数名称映射
INDEX_NAMES = {
    'sh000300': '沪深300',
    'sh000016': '上证50',
    'sh000905': '中证500',
    'sh000688': '科创50',
    'sz399006': '创业板指',
    'sh000852': '中证1000',
    'IXIC': '纳斯达克综合',
    'SPX': '标普500',
    'FTSE': '富时100',
    'DAX': '德国DAX',
    'N225': '日经225',
    'HSI': '恒生指数'
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
            
            # 转换数值列为正确的数据类型
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 删除无效数据（收盘价为NaN的行）
            df = df.dropna(subset=['close'])
            
            # 按日期排序并去重（保留最后一条）
            df = df.sort_values('date')
            df = df.drop_duplicates(subset=['date'], keep='last')
            df = df.reset_index(drop=True)
            
            return df
        
        return None
        
    except Exception as e:
        print(f"获取历史数据失败 {symbol}: {e}")
        return None


# 海外指数代码映射 (内部代码 -> Yahoo Finance代码)
YAHOO_SYMBOLS = {
    'IXIC': '^IXIC',      # 纳斯达克综合指数
    'SPX': '^GSPC',       # 标普500
    'FTSE': '^FTSE',      # 富时100
    'DAX': '^GDAXI',      # 德国DAX
    'N225': '^N225',      # 日经225
    'HSI': '^HSI',        # 恒生指数
}

# 海外指数创立日期
OVERSEAS_INDEX_DATES = {
    'IXIC': '1971-02-05',  # 纳斯达克综合指数
    'SPX': '1950-01-03',   # 标普500
    'FTSE': '1984-01-03',  # 富时100
    'DAX': '1987-11-30',   # 德国DAX
    'N225': '1984-01-04',   # 日经225
    'HSI': '1967-11-24'    # 恒生指数
}


def fetch_index_history_from_yahoo(symbol, start_date=None, end_date=None, max_retries=3):
    """
    从Yahoo Finance获取海外指数历史数据
    
    参数:
        symbol: 海外指数代码，如 IXIC, SPX, HSI
        start_date: 开始日期，格式 YYYY-MM-DD
        end_date: 结束日期，格式 YYYY-MM-DD
        max_retries: 最大重试次数
    
    返回:
        DataFrame 包含日期、开盘、收盘、最高、最低、成交量
    """
    import time as time_module
    
    # 检查是否是海外指数
    if symbol not in YAHOO_SYMBOLS:
        return None
    
    yahoo_symbol = YAHOO_SYMBOLS[symbol]
    
    # 设置默认日期范围
    if not start_date:
        start_date = OVERSEAS_INDEX_DATES.get(symbol, '2000-01-01')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
    end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())
    
    for attempt in range(max_retries):
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
            params = {
                'period1': start_ts,
                'period2': end_ts,
                'interval': '1d',
                'events': 'history'
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://finance.yahoo.com/'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code != 200:
                if attempt < max_retries - 1:
                    time_module.sleep(2)
                    continue
                return None
            
            data = response.json()
            result = data.get('chart', {}).get('result', [])
            
            if not result:
                if attempt < max_retries - 1:
                    time_module.sleep(2)
                    continue
                return None
            
            chart_data = result[0]
            timestamps = chart_data.get('timestamp', [])
            
            if not timestamps:
                if attempt < max_retries - 1:
                    time_module.sleep(2)
                    continue
                return None
            
            # 解析OHLC数据
            quotes = chart_data.get('indicators', {}).get('quote', [{}])[0]
            opens = quotes.get('open', [])
            highs = quotes.get('high', [])
            lows = quotes.get('low', [])
            closes = quotes.get('close', [])
            volumes = quotes.get('volume', [0] * len(timestamps))
            
            parsed_data = []
            for i, ts in enumerate(timestamps):
                try:
                    date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                    close_val = closes[i] if i < len(closes) and closes[i] is not None else 0
                    
                    if close_val == 0:
                        continue
                    
                    parsed_data.append({
                        'date': date_str,
                        'open': opens[i] if i < len(opens) and opens[i] is not None else close_val,
                        'high': highs[i] if i < len(highs) and highs[i] is not None else close_val,
                        'low': lows[i] if i < len(lows) and lows[i] is not None else close_val,
                        'close': close_val,
                        'volume': volumes[i] if i < len(volumes) else 0,
                        'amount': 0
                    })
                except Exception:
                    continue
            
            if parsed_data:
                df = pd.DataFrame(parsed_data)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                return df
            
            if attempt < max_retries - 1:
                time_module.sleep(2)
                continue
            
            return None
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time_module.sleep(2)
                continue
            return None
        except Exception as e:
            if attempt < max_retries - 1:
                time_module.sleep(2)
                continue
            print(f"Yahoo Finance获取失败 {symbol}: {e}")
            return None
    
    return None


def fetch_index_history_from_eastmoney(symbol, start_date=None, end_date=None, max_retries=5):
    """
    从东方财富获取指数历史数据
    优先数据源（数据最完整）
    """
    import time as time_module
    
    for attempt in range(max_retries):
        try:
            # 东方财富API
            url = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
            
            # 转换代码格式
            if symbol.startswith('sh'):
                secid = f"1.{symbol[2:]}"
            elif symbol.startswith('sz'):
                secid = f"0.{symbol[2:]}"
            else:
                secid = symbol
            
            if not start_date:
                start_date_str = INDEX_START_DATES.get(symbol, '20100101')
            else:
                start_date_str = start_date.replace('-', '')
            
            if not end_date:
                end_date_str = datetime.now().strftime('%Y%m%d')
            else:
                end_date_str = end_date.replace('-', '')
            
            params = {
                'secid': secid,
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'fields1': 'f1,f2,f3,f4,f5,f6',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
                'klt': 101,  # 日线
                'fqt': 0,    # 不复权
                'beg': start_date_str,
                'end': end_date_str,
                'smplmt': 100000,  # 获取所有数据
                '_': int(datetime.now().timestamp() * 1000)
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://finance.eastmoney.com',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            # 检查响应状态
            if response.status_code != 200:
                if attempt < max_retries - 1:
                    time_module.sleep(2)
                    continue
                return None
            
            # 检查响应是否为空
            response_text = response.text.strip()
            if not response_text:
                if attempt < max_retries - 1:
                    time_module.sleep(2)
                    continue
                return None
            
            data = response.json()
            
            if data.get('data') and data['data'].get('klines'):
                klines = data['data']['klines']
                
                # 解析K线数据
                parsed_data = []
                for line in klines:
                    parts = line.split(',')
                    if len(parts) >= 6:
                        try:
                            open_val = float(parts[1]) if parts[1] and parts[1].strip() else 0.0
                            close_val = float(parts[2]) if parts[2] and parts[2].strip() else 0.0
                            low_val = float(parts[3]) if parts[3] and parts[3].strip() else 0.0
                            high_val = float(parts[4]) if parts[4] and parts[4].strip() else 0.0
                            volume_val = float(parts[5]) if parts[5] and parts[5].strip() else 0.0
                            amount_val = float(parts[6]) if len(parts) > 6 and parts[6] and parts[6].strip() else 0.0
                            
                            if close_val == 0 or not parts[0]:
                                continue
                                
                            parsed_data.append({
                                'date': parts[0],
                                'open': open_val,
                                'close': close_val,
                                'low': low_val,
                                'high': high_val,
                                'volume': volume_val,
                                'amount': amount_val
                            })
                        except (ValueError, IndexError):
                            continue
                
                if parsed_data:
                    df = pd.DataFrame(parsed_data)
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date')
                    return df
                else:
                    if attempt < max_retries - 1:
                        time_module.sleep(1)
                        continue
                    return None
            
            # 如果数据为空，重试
            if attempt < max_retries - 1:
                time_module.sleep(1)
                continue
            
            return None
            
        except Exception as e:
            if attempt < max_retries - 1:
                time_module.sleep(1)
                continue
            print(f"东方财富数据获取失败 {symbol}: {e}")
            return None
    
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
    
    根据指数类型选择最优数据源：
    - A股指数：东方财富 -> 新浪 -> 错误
    - 海外指数：雅虎财经 -> 错误
    
    参数:
        symbol: 指数代码
        use_mock: 是否使用模拟数据
    
    返回:
        DataFrame 或 None
    """
    if use_mock:
        return generate_mock_history(symbol)
    
    # 判断是A股还是海外指数
    is_overseas = symbol in YAHOO_SYMBOLS
    
    if is_overseas:
        # 海外指数：使用雅虎财经
        print(f"正在获取海外指数 {symbol} 数据（使用雅虎财经）...")
        df = fetch_index_history_from_yahoo(symbol)
        
        if df is not None and len(df) > 0:
            print(f"成功从雅虎财经获取 {symbol} 历史数据，共 {len(df)} 条")
            return df
        
        # 雅虎财经失败，返回错误提示
        print(f"无法获取 {symbol} 海外指数数据，请检查网络连接")
        return None
    else:
        # A股指数：东方财富 -> 新浪 -> 错误
        df = fetch_index_history_from_eastmoney(symbol)
        
        if df is not None and len(df) > 0:
            print(f"成功从东方财富获取 {symbol} 历史数据，共 {len(df)} 条")
            return df
        
        # 备用：新浪
        df = fetch_index_history_from_sina(symbol)
        
        if df is not None and len(df) > 0:
            print(f"成功从新浪获取 {symbol} 历史数据，共 {len(df)} 条")
            return df
        
        # 都失败，返回错误提示
        print(f"无法获取 {symbol} 数据，请检查网络连接")
        return None


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
