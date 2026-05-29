#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指数基金定投助手 - 后端API服务
提供实时行情、历史估值、综合评分等功能
"""

import os
import json
import time
import random
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import requests

from history_data import get_index_history, calculate_pe_from_price, INDEX_NAMES, INDEX_START_DATES
from database import (
    init_database, add_record, get_records, delete_record, get_stats,
    save_alert_settings, get_alert_settings,
    save_stop_settings, get_stop_settings, get_all_stop_settings
)

# 初始化数据库
init_database()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# 配置 - 包含A股和海外主要指数
INDEX_LIST = {
    # A股指数
    'sh000300': {'name': '沪深300', 'type': '宽基', 'risk': '中', 'region': 'A股'},
    'sh000016': {'name': '上证50', 'type': '宽基', 'risk': '低', 'region': 'A股'},
    'sh000905': {'name': '中证500', 'type': '宽基', 'risk': '中高', 'region': 'A股'},
    'sh000688': {'name': '科创50', 'type': '科技', 'risk': '高', 'region': 'A股'},
    'sz399006': {'name': '创业板指', 'type': '成长', 'risk': '高', 'region': 'A股'},
    'sh000852': {'name': '中证1000', 'type': '小盘', 'risk': '高', 'region': 'A股'},
    'sh000001': {'name': '上证指数', 'type': '综合', 'risk': '中', 'region': 'A股'},
    'sz399001': {'name': '深证成指', 'type': '综合', 'risk': '中', 'region': 'A股'},
    # 海外指数（模拟数据）
    'IXIC': {'name': '纳斯达克100', 'type': '科技', 'risk': '高', 'region': '美股', 'currency': 'USD'},
    'SPX': {'name': '标普500', 'type': '综合', 'risk': '中', 'region': '美股', 'currency': 'USD'},
    'FTSE': {'name': '英国富时100', 'type': '综合', 'risk': '中', 'region': '欧洲', 'currency': 'GBP'},
    'DAX': {'name': '德国DAX', 'type': '综合', 'risk': '中', 'region': '欧洲', 'currency': 'EUR'},
    'N225': {'name': '日经225', 'type': '综合', 'risk': '中', 'region': '亚太', 'currency': 'JPY'},
    'HSI': {'name': '恒生指数', 'type': '综合', 'risk': '中高', 'region': '港股', 'currency': 'HKD'}
}

# PE估值历史范围
PE_HISTORY = {
    'sh000300': {'current': 14.18, 'min': 10, 'max': 18, 'avg': 13.5},
    'sh000016': {'current': 11.5, 'min': 8, 'max': 15, 'avg': 11},
    'sh000905': {'current': 22.5, 'min': 15, 'max': 35, 'avg': 25},
    'sh000688': {'current': 65, 'min': 35, 'max': 85, 'avg': 60},
    'sz399006': {'current': 28, 'min': 25, 'max': 60, 'avg': 42},
    'sh000852': {'current': 32, 'min': 20, 'max': 50, 'avg': 35},
    'sh000001': {'current': 13.5, 'min': 10, 'max': 20, 'avg': 14},
    'sz399001': {'current': 25, 'min': 18, 'max': 40, 'avg': 25},
    # 海外指数PE范围（模拟）
    'IXIC': {'current': 35, 'min': 20, 'max': 50, 'avg': 30},
    'SPX': {'current': 22, 'min': 15, 'max': 30, 'avg': 20},
    'FTSE': {'current': 15, 'min': 10, 'max': 22, 'avg': 14},
    'DAX': {'current': 15, 'min': 10, 'max': 25, 'avg': 14},
    'N225': {'current': 18, 'min': 12, 'max': 30, 'avg': 18},
    'HSI': {'current': 12, 'min': 8, 'max': 18, 'avg': 12}
}

# 缓存
cache = {
    'quotes': {'data': None, 'time': 0},
    'history': {}
}

CACHE_TIME = 60  # 缓存时间（秒）


def get_cache(key):
    """获取缓存"""
    if key in cache and cache[key]['data']:
        if time.time() - cache[key]['time'] < CACHE_TIME:
            return cache[key]['data']
    return None


def set_cache(key, data):
    """设置缓存"""
    cache[key] = {'data': data, 'time': time.time()}


def fetch_sina_quotes():
    """从新浪获取实时行情（A股）+ 海外指数模拟数据"""
    cached = get_cache('quotes')
    if cached:
        return cached
    
    data = []
    
    # 获取A股指数（新浪）
    cn_codes = [k for k, v in INDEX_LIST.items() if v.get('region') == 'A股']
    
    for code in cn_codes:
        try:
            url = f'https://hq.sinajs.cn/list={code}'
            headers = {
                'Referer': 'https://finance.sina.com.cn',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            response.encoding = 'gbk'
            
            line = response.text.strip()
            if '=' in line and '"' in line:
                values = line.split('"')[1].split(',')
                
                if len(values) >= 4:
                    current_price = float(values[3]) if values[3] else 0
                    prev_close = float(values[2]) if values[2] else 0
                    
                    if prev_close > 0:
                        change = current_price - prev_close
                        change_percent = (change / prev_close) * 100
                    else:
                        change = 0
                        change_percent = 0
                    
                    item = {
                        'code': code,
                        'name': INDEX_LIST[code]['name'],
                        'type': INDEX_LIST[code]['type'],
                        'risk': INDEX_LIST[code]['risk'],
                        'region': INDEX_LIST[code].get('region', 'A股'),
                        'price': round(current_price, 2),
                        'change': round(change, 2),
                        'changePercent': round(change_percent, 2),
                        'source': 'sina'
                    }
                    
                    # 添加PE和分位数据
                    pe_info = PE_HISTORY.get(code, {})
                    item['pe'] = pe_info.get('current', 0)
                    item['peMin'] = pe_info.get('min', 0)
                    item['peMax'] = pe_info.get('max', 0)
                    
                    if pe_info:
                        range_val = pe_info['max'] - pe_info['min']
                        position = pe_info['current'] - pe_info['min']
                        item['pePercentile'] = round((position / range_val) * 100) if range_val > 0 else 50
                    else:
                        item['pePercentile'] = 50
                    
                    data.append(item)
        except Exception as e:
            print(f"获取 {code} 数据失败: {e}")
            continue
    
    # 添加海外指数 - 使用腾讯财经和新浪国际获取真实数据
    global_data_sources = {
        # 腾讯财经数据源（美股、港股）
        'IXIC': {'qq_code': 'usIXIC', 'name': '纳斯达克综合', 'sina_code': None},
        'SPX':  {'qq_code': 'us.INX', 'name': '标普500', 'sina_code': None},
        'HSI':  {'qq_code': 'r_hkHSI', 'name': '恒生指数', 'sina_code': 'rt_hkHSI'},
        # 新浪国际数据源（欧日）
        'FTSE': {'qq_code': None, 'name': '富时100', 'sina_code': 'int_ftse'},
        'N225': {'qq_code': None, 'name': '日经225', 'sina_code': 'int_nikkei'},
        # 德国DAX暂无免费源，使用模拟
        'DAX':  {'qq_code': None, 'name': '德国DAX', 'sina_code': None},
    }
    
    # 腾讯财经批量获取（一次请求多个）
    qq_codes = [v['qq_code'] for v in global_data_sources.values() if v['qq_code']]
    # 腾讯返回的parts[2]是原始代码如.NDX、.INX，需要建立映射
    qq_code_to_index = {}
    for k, v in global_data_sources.items():
        if v['qq_code']:
            qq_code_to_index[v['qq_code']] = k
    # 同时映射原始代码（腾讯返回的parts[2]）
    raw_code_map = {
            '.NDX': 'IXIC', '.IXIC': 'IXIC', '.DJI': 'IXIC', '.INX': 'SPX',
            'HSI': 'HSI', 'r_hkHSI': 'HSI'
        }
    
    if qq_codes:
        try:
            qq_url = f'https://qt.gtimg.cn/q={",".join(qq_codes)}'
            qq_headers = {
                'Referer': 'https://finance.qq.com',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            qq_response = requests.get(qq_url, headers=qq_headers, timeout=10)
            qq_response.encoding = 'gbk'
            qq_text = qq_response.text
            
            # 如果gbk解码失败，尝试utf-8
            if '�' in qq_text:
                try:
                    qq_text = qq_response.content.decode('utf-8')
                except:
                    qq_text = qq_response.content.decode('latin-1')
            
            for line in qq_text.strip().split(';'):
                line = line.strip()
                if not line or '~' not in line:
                    continue
                try:
                    content = line.split('="')[1].rstrip('\";')
                    parts = content.split('~')
                    if len(parts) < 35:
                        continue
                    
                    qq_code = parts[2]
                    index_code = qq_code_to_index.get(qq_code) or raw_code_map.get(qq_code)
                    if not index_code:
                        continue
                    
                    info = INDEX_LIST.get(index_code, {})
                    pe_info = PE_HISTORY.get(index_code, {})
                    
                    price = float(parts[3]) if parts[3] else 0
                    prev_close = float(parts[4]) if parts[4] else 0
                    change_pct = float(parts[32]) if parts[32] else 0
                    high = float(parts[33]) if parts[33] else 0
                    low = float(parts[34]) if parts[34] else 0
                    currency = parts[37] if len(parts) > 37 else info.get('currency', 'USD')
                    
                    if prev_close > 0:
                        change = price - prev_close
                    else:
                        change = price * change_pct / 100
                    
                    item = {
                        'code': index_code,
                        'name': info.get('name', parts[1]),
                        'type': info.get('type', '综合'),
                        'risk': info.get('risk', '中'),
                        'region': info.get('region', '海外'),
                        'currency': currency,
                        'price': round(price, 2),
                        'change': round(change, 2),
                        'changePercent': round(change_pct, 2),
                        'high': round(high, 2),
                        'low': round(low, 2),
                        'source': 'qq'
                    }
                    
                    item['pe'] = pe_info.get('current', 20)
                    item['peMin'] = pe_info.get('min', 10)
                    item['peMax'] = pe_info.get('max', 30)
                    
                    if pe_info:
                        range_val = pe_info['max'] - pe_info['min']
                        position = pe_info['current'] - pe_info['min']
                        item['pePercentile'] = round((position / range_val) * 100) if range_val > 0 else 50
                    else:
                        item['pePercentile'] = 50
                    
                    data.append(item)
                    print(f"  ✅ 腾讯获取 {item['name']}: {item['price']} ({change_pct}%)")
                    
                except Exception as e:
                    print(f"  解析腾讯数据失败: {e}")
                    continue
        except Exception as e:
            print(f"腾讯财经请求失败: {e}")
    
    # 新浪国际数据源（富时100、日经225）
    sina_int_codes = [(k, v['sina_code']) for k, v in global_data_sources.items() 
                      if v['sina_code'] and k not in [d.get('code') for d in data]]
    
    for index_code, sina_code in sina_int_codes:
        try:
            sina_url = f'https://hq.sinajs.cn/list={sina_code}'
            sina_headers = {
                'Referer': 'https://finance.sina.com.cn',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            sina_response = requests.get(sina_url, headers=sina_headers, timeout=10)
            sina_response.encoding = 'gbk'
            
            line = sina_response.text.strip()
            if '=' in line and '"' in line:
                values = line.split('"')[1].split(',')
                
                if len(values) >= 4:
                    info = INDEX_LIST.get(index_code, {})
                    pe_info = PE_HISTORY.get(index_code, {})
                    
                    price = float(values[1]) if values[1] else 0
                    change = float(values[2]) if values[2] else 0
                    change_pct = float(values[3]) if values[3] else 0
                    
                    item = {
                        'code': index_code,
                        'name': info.get('name', index_code),
                        'type': info.get('type', '综合'),
                        'risk': info.get('risk', '中'),
                        'region': info.get('region', '海外'),
                        'currency': info.get('currency', ''),
                        'price': round(price, 2),
                        'change': round(change, 2),
                        'changePercent': round(change_pct, 2),
                        'source': 'sina_int'
                    }
                    
                    item['pe'] = pe_info.get('current', 20)
                    item['peMin'] = pe_info.get('min', 10)
                    item['peMax'] = pe_info.get('max', 30)
                    
                    if pe_info:
                        range_val = pe_info['max'] - pe_info['min']
                        position = pe_info['current'] - pe_info['min']
                        item['pePercentile'] = round((position / range_val) * 100) if range_val > 0 else 50
                    else:
                        item['pePercentile'] = 50
                    
                    data.append(item)
                    print(f"  ✅ 新浪获取 {item['name']}: {item['price']} ({change_pct}%)")
                    
        except Exception as e:
            print(f"  新浪国际获取 {index_code} 失败: {e}")
    
    result = {
        'success': True,
        'data': data,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source': 'mixed'
    }
    
    set_cache('quotes', result)
    return result


def calculate_pe_percentile(code):
    """计算PE百分位"""
    pe_info = PE_HISTORY.get(code, {})
    if not pe_info:
        return 50
    
    range_val = pe_info['max'] - pe_info['min']
    position = pe_info['current'] - pe_info['min']
    return round((position / range_val) * 100) if range_val > 0 else 50


def calculate_score(item):
    """计算综合评分"""
    score = 50
    pe_percentile = item.get('pePercentile', 50)
    risk = item.get('risk', '中')
    change_percent = item.get('changePercent', 0)
    
    # 估值评分 (40分)
    if pe_percentile < 20:
        score += 20
    elif pe_percentile < 30:
        score += 15
    elif pe_percentile < 40:
        score += 10
    elif pe_percentile < 50:
        score += 5
    elif pe_percentile > 80:
        score -= 15
    elif pe_percentile > 70:
        score -= 10
    elif pe_percentile > 60:
        score -= 5
    
    # 趋势评分 (20分)
    if change_percent > 2:
        score += 10
    elif change_percent > 0:
        score += 5
    elif change_percent < -2:
        score -= 5
    
    # 风险调整 (10分)
    if risk == '低':
        score += 5
    elif risk == '高':
        score -= 3
    
    return max(0, min(100, score))


def get_recommendation(pe_percentile):
    """获取定投建议"""
    if pe_percentile < 30:
        return {
            'action': 'buy-more',
            'title': '💚 积极定投期',
            'multiplier': 1.5,
            'message': '当前估值偏低，建议加倍定投',
            'reason': 'PE处于历史低位，是积累筹码的好时机'
        }
    elif pe_percentile < 70:
        return {
            'action': 'normal',
            'title': '💛 正常定投期',
            'multiplier': 1.0,
            'message': '估值合理，建议正常定投',
            'reason': '估值处于合理区间，按计划执行即可'
        }
    else:
        return {
            'action': 'reduce',
            'title': '❤️ 谨慎期/止盈期',
            'multiplier': 0.5,
            'message': '估值偏高，建议减少定投或止盈',
            'reason': '估值处于高位，注意控制风险'
        }


def generate_history_data(code, days=30):
    """生成历史数据（模拟）"""
    key = f'history_{code}'
    cached = cache['history'].get(key)
    
    if cached and time.time() - cached['time'] < 3600:
        return cached['data']
    
    pe_info = PE_HISTORY.get(code, {})
    if not pe_info:
        return []
    
    history = []
    today = datetime.now()
    
    for i in range(days, 0, -1):
        date = today - timedelta(days=i)
        
        # 模拟历史波动
        random_factor = 0.95 + random.random() * 0.1
        pe = pe_info['current'] * random_factor
        
        history.append({
            'date': date.strftime('%Y-%m-%d'),
            'pe': round(pe, 2),
            'percentile': calculate_pe_percentile(code)
        })
    
    cache['history'][key] = {'data': history, 'time': time.time()}
    return history


# ============== API 路由 ==============

@app.route('/')
def index():
    """前端页面"""
    return render_template('index.html')

@app.route('/app.js')
def serve_js():
    """提供JS文件"""
    return send_from_directory('static', 'app.js', mimetype='application/javascript')


@app.route('/api/quotes')
def get_quotes():
    """获取所有指数实时行情"""
    result = fetch_sina_quotes()
    return jsonify(result)


@app.route('/api/quote/<code>')
def get_quote(code):
    """获取单个指数详情"""
    result = fetch_sina_quotes()
    
    for item in result.get('data', []):
        if item['code'] == code:
            item['score'] = calculate_score(item)
            item['recommendation'] = get_recommendation(item['pePercentile'])
            return jsonify({
                'success': True,
                'data': item
            })
    
    return jsonify({
        'success': False,
        'error': f'指数 {code} 不存在'
    })


@app.route('/api/scores')
def get_scores():
    """获取所有指数综合评分"""
    result = fetch_sina_quotes()
    
    scored_data = []
    for item in result.get('data', []):
        item['score'] = calculate_score(item)
        scored_data.append(item)
    
    # 按评分排序
    scored_data.sort(key=lambda x: x['score'], reverse=True)
    
    return jsonify({
        'success': True,
        'data': scored_data,
        'timestamp': result.get('timestamp')
    })


@app.route('/api/recommendations')
def get_recommendations():
    """获取定投建议"""
    result = fetch_sina_quotes()
    
    # 找出评分最高的指数
    best_index = None
    best_score = 0
    
    for item in result.get('data', []):
        score = calculate_score(item)
        if score > best_score:
            best_score = score
            best_index = item
    
    if not best_index:
        return jsonify({
            'success': False,
            'error': '无法获取数据'
        })
    
    best_index['score'] = best_score
    recommendation = get_recommendation(best_index['pePercentile'])
    
    return jsonify({
        'success': True,
        'data': {
            'focusIndex': best_index,
            'recommendation': recommendation,
            'allIndices': result.get('data', [])
        },
        'timestamp': result.get('timestamp')
    })


@app.route('/api/history/<code>')
def get_history(code):
    """获取指数历史数据（创立以来）"""
    if code not in INDEX_LIST:
        return jsonify({
            'success': False,
            'error': f'指数 {code} 不存在'
        })
    
    # 获取完整历史数据（优先使用真实数据）
    df = get_index_history(code, use_mock=False)
    
    if df is None or len(df) == 0:
        return jsonify({
            'success': False,
            'error': '无法获取历史数据'
        })
    
    # 添加PE数据
    df = calculate_pe_from_price(df, code)
    
    # 转换为JSON格式
    history_data = []
    for _, row in df.iterrows():
        history_data.append({
            'date': row['date'] if isinstance(row['date'], str) else row['date'].strftime('%Y-%m-%d'),
            'open': float(row['open']),
            'close': float(row['close']),
            'high': float(row['high']),
            'low': float(row['low']),
            'volume': int(row['volume']),
            'pe': float(row['pe']),
            'pePercentile': float(row['pe_percentile'])
        })
    
    return jsonify({
        'success': True,
        'code': code,
        'name': INDEX_LIST[code]['name'],
        'startDate': INDEX_START_DATES.get(code, '2010-01-01'),
        'totalDays': len(history_data),
        'data': history_data
    })


@app.route('/api/history/summary')
def get_history_summary():
    """获取所有指数历史数据摘要"""
    summary = []
    
    for code in INDEX_LIST.keys():
        df = get_index_history(code, use_mock=False)
        if df is not None and len(df) > 0:
            df = calculate_pe_from_price(df, code)
            
            summary.append({
                'code': code,
                'name': INDEX_LIST[code]['name'],
                'startDate': INDEX_START_DATES.get(code, '2010-01-01'),
                'totalDays': len(df),
                'latestPrice': float(df['close'].iloc[-1]),
                'latestPE': float(df['pe'].iloc[-1]),
                'avgPE': float(df['pe'].mean()),
                'minPE': float(df['pe'].min()),
                'maxPE': float(df['pe'].max()),
                'currentPercentile': float(df['pe_percentile'].iloc[-1])
            })
    
    return jsonify({
        'success': True,
        'data': summary
    })


@app.route('/api/strategies')
def get_strategies():
    """获取配置策略"""
    strategies = {
        'conservative': {
            'name': '保守型策略',
            'description': '追求稳定收益，风险承受能力较低',
            'allocation': [
                {'code': 'sh000300', 'name': '沪深300', 'percent': 50},
                {'code': 'sh000905', 'name': '中证500', 'percent': 30},
                {'code': 'sh000016', 'name': '上证50', 'percent': 20}
            ],
            'expectedReturn': '6-9%',
            'riskLevel': '低'
        },
        'balanced': {
            'name': '平衡型策略',
            'description': '希望收益与风险平衡',
            'allocation': [
                {'code': 'sh000300', 'name': '沪深300', 'percent': 40},
                {'code': 'sz399006', 'name': '创业板指', 'percent': 30},
                {'code': 'sh000905', 'name': '中证500', 'percent': 20},
                {'code': 'sh000016', 'name': '红利指数', 'percent': 10}
            ],
            'expectedReturn': '8-12%',
            'riskLevel': '中'
        },
        'aggressive': {
            'name': '积极型策略',
            'description': '追求高收益，能承受较大波动',
            'allocation': [
                {'code': 'sz399006', 'name': '创业板指', 'percent': 30},
                {'code': 'sh000688', 'name': '科创50', 'percent': 25},
                {'code': 'sh000852', 'name': '中证1000', 'percent': 25},
                {'code': 'sh000905', 'name': '中证500', 'percent': 20}
            ],
            'expectedReturn': '10-15%',
            'riskLevel': '高'
        }
    }
    
    return jsonify({
        'success': True,
        'data': strategies
    })


@app.route('/api/calculator')
def calculate_dca():
    """定投收益计算"""
    monthly = request.args.get('monthly', 1000, type=int)
    years = request.args.get('years', 5, type=int)
    return_rate = request.args.get('return', 8, type=float)
    
    months = years * 12
    monthly_rate = return_rate / 100 / 12
    
    total_principal = monthly * months
    total_asset = monthly * ((1 + monthly_rate) ** months - 1) / monthly_rate * (1 + monthly_rate)
    total_profit = total_asset - total_principal
    profit_percent = (total_profit / total_principal) * 100
    
    return jsonify({
        'success': True,
        'input': {
            'monthly': monthly,
            'years': years,
            'returnRate': return_rate
        },
        'result': {
            'totalPrincipal': round(total_principal, 2),
            'totalAsset': round(total_asset, 2),
            'totalProfit': round(total_profit, 2),
            'profitPercent': round(profit_percent, 2)
        }
    })


@app.route('/api/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


# ============== 数据库API ==============

@app.route('/api/records', methods=['GET'])
def get_all_records():
    """获取所有定投记录"""
    try:
        records = get_records()
        stats = get_stats()
        return jsonify({
            'success': True,
            'records': records,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/records', methods=['POST'])
def create_record():
    """添加定投记录"""
    try:
        data = request.get_json()
        record_id = add_record(
            index_code=data['index_code'],
            index_name=data['index_name'],
            amount=data['amount'],
            invest_date=data['invest_date'],
            note=data.get('note', ''),
            buy_price=data.get('buy_price', 0),
            buy_index_point=data.get('buy_index_point', 0)
        )
        return jsonify({
            'success': True,
            'id': record_id,
            'message': '记录添加成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/records/<int:record_id>', methods=['DELETE'])
def remove_record(record_id):
    """删除定投记录"""
    try:
        delete_record(record_id)
        return jsonify({
            'success': True,
            'message': '记录已删除'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """获取定投统计"""
    try:
        stats = get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/settings/alert', methods=['GET'])
def get_alert():
    """获取估值提醒设置"""
    try:
        settings = get_alert_settings()
        return jsonify({
            'success': True,
            'settings': settings
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/settings/alert', methods=['POST'])
def save_alert():
    """保存估值提醒设置"""
    try:
        data = request.get_json()
        save_alert_settings(
            pe_threshold=data.get('pe_threshold', 30),
            invest_day=data.get('invest_day', 1),
            enabled=data.get('enabled', 1)
        )
        return jsonify({
            'success': True,
            'message': '设置已保存'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/settings/stop', methods=['GET'])
def get_stop():
    """获取止盈止损设置"""
    try:
        index_code = request.args.get('index_code', 'sh000300')
        settings = get_stop_settings(index_code)
        return jsonify({
            'success': True,
            'settings': settings
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/settings/stop', methods=['POST'])
def save_stop():
    """保存止盈止损设置"""
    try:
        data = request.get_json()
        save_stop_settings(
            index_code=data.get('index_code', 'sh000300'),
            stop_profit=data.get('stop_profit', 15),
            stop_loss=data.get('stop_loss', -10)
        )
        return jsonify({
            'success': True,
            'message': '设置已保存'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/alerts/check', methods=['GET'])
def check_alerts():
    """检查止盈止损提醒 - 返回各指数当前价格"""
    try:
        # 获取所有指数的当前价格
        quotes_response = get_quotes()
        
        # 如果get_quotes返回Response对象，需要解析
        if hasattr(quotes_response, 'get_json'):
            quotes_data = quotes_response.get_json()
        else:
            quotes_data = quotes_response
            
        if quotes_data and quotes_data.get('data'):
            prices = {}
            for item in quotes_data['data']:
                prices[item['code']] = {
                    'price': item['price'],
                    'changePercent': item.get('changePercent', 0)
                }
            return jsonify({
                'success': True,
                'prices': prices
            })
        return jsonify({
            'success': False,
            'error': '无法获取行情数据'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ============== 云端备份API ==============

import hashlib
import os

# 云端备份存储目录
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

def generate_backup_code():
    """生成唯一的备份码"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = str(random.randint(1000, 9999))
    raw = f"{timestamp}{random_str}"
    # 生成6位字母数字组合
    code = hashlib.md5(raw.encode()).hexdigest()[:6].upper()
    return code

@app.route('/api/backup', methods=['POST'])
def create_backup():
    """创建云端备份"""
    try:
        data = request.get_json()
        if not data or 'records' not in data:
            return jsonify({'success': False, 'error': '没有数据可备份'})
        
        records = data['records']
        settings = data.get('settings', {})
        
        # 生成备份码
        backup_code = generate_backup_code()
        
        # 构建备份数据
        backup_data = {
            'backup_code': backup_code,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'records_count': len(records),
            'records': records,
            'settings': settings,
            'version': '1.0'
        }
        
        # 保存到文件
        backup_file = os.path.join(BACKUP_DIR, f'{backup_code}.json')
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'backup_code': backup_code,
            'message': f'备份成功！共备份 {len(records)} 条记录',
            'created_at': backup_data['created_at']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/backup/<code>', methods=['GET'])
def get_backup(code):
    """获取云端备份"""
    try:
        backup_file = os.path.join(BACKUP_DIR, f'{code.upper()}.json')
        
        if not os.path.exists(backup_file):
            return jsonify({'success': False, 'error': '备份码不存在或已过期'})
        
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        return jsonify({
            'success': True,
            'backup_code': backup_data['backup_code'],
            'created_at': backup_data['created_at'],
            'records_count': backup_data['records_count'],
            'records': backup_data['records'],
            'settings': backup_data.get('settings', {})
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/backup/<code>', methods=['DELETE'])
def delete_backup(code):
    """删除云端备份"""
    try:
        backup_file = os.path.join(BACKUP_DIR, f'{code.upper()}.json')
        
        if not os.path.exists(backup_file):
            return jsonify({'success': False, 'error': '备份码不存在'})
        
        os.remove(backup_file)
        
        return jsonify({
            'success': True,
            'message': f'备份 {code.upper()} 已删除'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/backup/list', methods=['GET'])
def list_backups():
    """列出所有备份（用于管理）"""
    try:
        backups = []
        for filename in os.listdir(BACKUP_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(BACKUP_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    backups.append({
                        'backup_code': data['backup_code'],
                        'created_at': data['created_at'],
                        'records_count': data['records_count']
                    })
        
        # 按时间倒序
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'success': True,
            'count': len(backups),
            'backups': backups
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ============== 启动服务 ==============

if __name__ == '__main__':
    print("=" * 50)
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print("📈 指数基金定投助手 - 后端API服务")
    print("=" * 50)
    print(f"🌐 访问地址: http://localhost:{port}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
