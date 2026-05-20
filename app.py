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

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# 配置
INDEX_LIST = {
    'sh000300': {'name': '沪深300', 'type': '宽基', 'risk': '中'},
    'sh000016': {'name': '上证50', 'type': '宽基', 'risk': '低'},
    'sh000905': {'name': '中证500', 'type': '宽基', 'risk': '中高'},
    'sh000688': {'name': '科创50', 'type': '科技', 'risk': '高'},
    'sz399006': {'name': '创业板指', 'type': '成长', 'risk': '高'},
    'sh000852': {'name': '中证1000', 'type': '小盘', 'risk': '高'}
}

# PE估值历史范围
PE_HISTORY = {
    'sh000300': {'current': 14.18, 'min': 10, 'max': 18, 'avg': 13.5},
    'sh000016': {'current': 11.5, 'min': 8, 'max': 15, 'avg': 11},
    'sh000905': {'current': 22.5, 'min': 15, 'max': 35, 'avg': 25},
    'sh000688': {'current': 65, 'min': 35, 'max': 85, 'avg': 60},
    'sz399006': {'current': 28, 'min': 25, 'max': 60, 'avg': 42},
    'sh000852': {'current': 32, 'min': 20, 'max': 50, 'avg': 35}
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
    """从新浪获取实时行情"""
    cached = get_cache('quotes')
    if cached:
        return cached
    
    codes = list(INDEX_LIST.keys())
    
    try:
        # 分别获取每个指数的数据，避免数据错位
        data = []
        for code in codes:
            try:
                url = f'https://hq.sinajs.cn/list={code}'
                headers = {
                    'Referer': 'https://finance.sina.com.cn',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                response.encoding = 'gbk'
                
                line = response.text.strip()
                if '=' in line and '"' in line:
                    values = line.split('"')[1].split(',')
                    
                    if len(values) >= 3:
                        # 新浪API返回格式：指数名称,今日开盘,昨日收盘,当前点数,今日最高,今日最低,... 
                        # values[0] = 指数名称
                        # values[1] = 今日开盘
                        # values[2] = 昨日收盘
                        # values[3] = 当前点数
                        # values[4] = 今日最高
                        # values[5] = 今日最低
                        
                        current_price = float(values[3]) if values[3] else 0
                        prev_close = float(values[2]) if values[2] else 0
                        
                        # 计算涨跌幅
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
                            'price': round(current_price, 2),
                            'change': round(change, 2),
                            'changePercent': round(change_percent, 2),
                            'volume': float(values[6]) if len(values) > 6 and values[6] else 0,
                            'amount': float(values[7]) if len(values) > 7 and values[7] else 0
                        }
                        
                        # 添加PE和分位数据
                        pe_info = PE_HISTORY.get(code, {})
                        item['pe'] = pe_info.get('current', 0)
                        item['peMin'] = pe_info.get('min', 0)
                        item['peMax'] = pe_info.get('max', 0)
                        
                        # 计算PE分位
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
        
        if len(data) > 0:
            result = {
                'success': True,
                'data': data,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'sina'
            }
            set_cache('quotes', result)
            return result
        else:
            raise Exception("无法获取任何指数数据")
        
    except Exception as e:
        print(f"Error fetching quotes: {e}")
        # 返回模拟数据作为降级
        mock_data = get_mock_data()
        return {
            'success': True,  # 仍然返回success，但使用模拟数据
            'data': mock_data,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'mock',
            'note': '使用模拟数据（API暂时不可用）'
        }


def get_mock_data():
    """获取模拟数据（当API失败时）"""
    data = []
    for code, info in INDEX_LIST.items():
        pe_info = PE_HISTORY.get(code, {})
        
        # 添加随机波动
        base_price = random.uniform(2000, 8000)
        change = random.uniform(-50, 50)
        
        item = {
            'code': code,
            'name': info['name'],
            'type': info['type'],
            'risk': info['risk'],
            'price': round(base_price, 2),
            'change': round(change, 2),
            'changePercent': round((change / base_price) * 100, 2),
            'volume': random.randint(100000000, 500000000),
            'amount': random.randint(1000000000, 5000000000),
            'pe': pe_info.get('current', 0),
            'peMin': pe_info.get('min', 0),
            'peMax': pe_info.get('max', 0),
            'pePercentile': calculate_pe_percentile(code)
        }
        data.append(item)
    
    return data


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
    
    # 获取完整历史数据
    df = get_index_history(code, use_mock=True)  # 使用模拟数据确保稳定性
    
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
        df = get_index_history(code, use_mock=True)
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


# ============== 启动服务 ==============

if __name__ == '__main__':
    print("=" * 50)
    print("📈 指数基金定投助手 - 后端API服务")
    print("=" * 50)
    print("🌐 访问地址: http://localhost:5000")
    print("📚 API文档: http://localhost:5000/")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
