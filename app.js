/**
 * 指数基金定投助手 - 主程序
 * 支持本地和后端API两种数据源模式
 */

// API配置
// 使用相对路径，前端和后端部署在同一服务上
const API_BASE_URL = '';  // 空字符串表示使用相对路径
const USE_API = true;  // 设为false则使用本地模拟数据
const API_TIMEOUT = 15000;  // API请求超时时间（毫秒）- 增加到15秒
const MAX_RETRIES = 3;  // 最大重试次数 - 增加到3次
const RETRY_DELAY = 1500;  // 重试间隔（毫秒）

console.log('[API配置] 使用相对路径模式');

// 指数配置
const INDEX_CONFIG = {
    'sh000300': { 
        name: '沪深300', 
        type: '宽基', 
        basePE: 12, 
        risk: '中',
        region: 'A股',
        description: 'A股核心资产，300家龙头企业',
        bestFor: '稳健型投资者，作为核心配置',
        fundOptions: ['华泰柏瑞沪深300ETF(510300)', '易方达沪深300ETF(510310)']
    },
    'sh000016': { 
        name: '上证50', 
        type: '宽基', 
        basePE: 10, 
        risk: '低',
        region: 'A股',
        description: '沪市超大盘蓝筹，金融消费为主',
        bestFor: '保守型投资者，追求稳定分红',
        fundOptions: ['华夏上证50ETF(510050)', '易方达上证50ETF(510100)']
    },
    'sh000905': { 
        name: '中证500', 
        type: '宽基', 
        basePE: 20, 
        risk: '中高',
        region: 'A股',
        description: '中小盘成长股代表',
        bestFor: '追求成长的投资者，分散配置',
        fundOptions: ['南方中证500ETF(510500)', '华夏中证500ETF(512500)']
    },
    'sh000688': { 
        name: '科创50', 
        type: '科技', 
        basePE: 50, 
        risk: '高',
        region: 'A股',
        description: '科创板龙头，硬科技方向',
        bestFor: '高风险承受者，看好科技创新',
        fundOptions: ['华夏科创50ETF(588000)', '易方达科创50ETF(588080)']
    },
    'sz399006': { 
        name: '创业板指', 
        type: '成长', 
        basePE: 35, 
        risk: '高',
        region: 'A股',
        description: '创业板100家成长企业',
        bestFor: '看好新兴产业，能承受波动',
        fundOptions: ['易方达创业板ETF(159915)', '华安创业板50ETF(159949)']
    },
    'sh000852': { 
        name: '中证1000', 
        type: '小盘', 
        basePE: 25, 
        risk: '高',
        region: 'A股',
        description: '小市值成长股',
        bestFor: '追求高收益，能承受高波动',
        fundOptions: ['南方中证1000ETF(512100)', '华夏中证1000ETF(159845)']
    },
    'sh000001': { 
        name: '上证指数', 
        type: '综合', 
        basePE: 13, 
        risk: '中',
        region: 'A股',
        description: '上海证券交易所综合指数',
        bestFor: '整体市场走势参考'
    },
    'sz399001': { 
        name: '深证成指', 
        type: '综合', 
        basePE: 22, 
        risk: '中',
        region: 'A股',
        description: '深圳证券交易所成分指数',
        bestFor: '深圳市场走势参考'
    },
    'IXIC': { 
        name: '纳斯达克100', 
        type: '科技', 
        basePE: 30, 
        risk: '高',
        region: '美股',
        currency: 'USD',
        description: '美国科技股旗舰指数',
        bestFor: '看好美国科技股，长期投资',
        fundOptions: ['纳指ETF(513100)', '广发纳指ETF(159941)']
    },
    'SPX': { 
        name: '标普500', 
        type: '综合', 
        basePE: 20, 
        risk: '中',
        region: '美股',
        currency: 'USD',
        description: '美国大盘股代表，覆盖500家上市公司',
        bestFor: '分散投资美国市场，稳健配置',
        fundOptions: ['标普500ETF(513500)', '博时标普500ETF(513400)']
    },
    'FTSE': { 
        name: '英国富时100', 
        type: '综合', 
        basePE: 14, 
        risk: '中',
        region: '欧洲',
        currency: 'GBP',
        description: '英国主板市场100家上市公司',
        bestFor: '欧洲市场配置'
    },
    'DAX': { 
        name: '德国DAX', 
        type: '综合', 
        basePE: 14, 
        risk: '中',
        region: '欧洲',
        currency: 'EUR',
        description: '德国30家蓝筹股指数',
        bestFor: '欧洲经济配置',
        fundOptions: ['德国ETF(513030)', '华安德国DAX ETF(513880)']
    },
    'N225': { 
        name: '日经225', 
        type: '综合', 
        basePE: 18, 
        risk: '中',
        region: '亚太',
        currency: 'JPY',
        description: '日本225家上市公司指数',
        bestFor: '日本市场配置',
        fundOptions: ['日经ETF(513520)', '华夏日经225ETF(157270)']
    },
    'HSI': { 
        name: '恒生指数', 
        type: '综合', 
        basePE: 12, 
        risk: '中高',
        region: '港股',
        currency: 'HKD',
        description: '香港交易所50家上市公司',
        bestFor: '配置中国概念股，回港上市',
        fundOptions: ['恒生ETF(159920)', '恒生科技ETF(513180)']
    }
};

// 图表实例
let peChart = null;
let priceChart = null;
let scoreChart = null;

// 从后端API获取数据（带超时和重试）
async function fetchFromAPI(endpoint, options = {}, retryCount = 0) {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);
        
        // 合并默认选项和传入的选项
        const fetchOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            signal: controller.signal,
            cache: 'no-cache',
            ...options
        };
        
        // 如果有 body 且是对象，转换为 JSON 字符串
        if (fetchOptions.body && typeof fetchOptions.body === 'object') {
            fetchOptions.body = JSON.stringify(fetchOptions.body);
        }
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, fetchOptions);
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`API请求失败: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // 验证返回数据格式
        if (!data || typeof data !== 'object') {
            throw new Error('API返回数据格式无效');
        }
        
        // 验证数据完整性 - 检查关键字段
        if (endpoint === '/api/quotes' && (!data.data || !Array.isArray(data.data) || data.data.length === 0)) {
            throw new Error('API返回数据为空');
        }
        
        return data;
        
    } catch (error) {
        console.error(`API请求错误 (${endpoint}):`, error.message);
        
        // 重试机制 - 使用指数退避
        if (retryCount < MAX_RETRIES) {
            const delay = RETRY_DELAY * Math.pow(2, retryCount);  // 指数退避: 1.5s, 3s, 6s
            console.log(`正在重试 (${retryCount + 1}/${MAX_RETRIES})，等待 ${delay}ms...`);
            await new Promise(resolve => setTimeout(resolve, delay));
            return fetchFromAPI(endpoint, options, retryCount + 1);
        }
        
        // 显示降级提示
        showDataSourceIndicator('local');
        return null;
    }
}

// 显示数据源指示器
function showDataSourceIndicator(source) {
    const updateTimeEl = document.getElementById('updateTime');
    if (updateTimeEl) {
        const existingIndicator = updateTimeEl.querySelector('.data-source-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }
        
        if (source === 'local') {
            const indicator = document.createElement('span');
            indicator.className = 'data-source-indicator';
            indicator.style.cssText = 'margin-left: 8px; font-size: 0.8rem; color: #f59e0b; font-weight: 500;';
            indicator.textContent = '(本地数据)';
            indicator.title = 'API连接失败，使用本地模拟数据';
            updateTimeEl.appendChild(indicator);
        }
    }
}

// 获取实时行情（优先后端API）
async function fetchQuotes() {
    if (USE_API) {
        const result = await fetchFromAPI('/api/quotes');
        if (result && result.success) {
            return {
                success: true,
                data: result.data,
                timestamp: result.timestamp
            };
        }
    }
    
    // API失败，返回null让调用方处理
    return null;
}

// 本地模拟数据
function getLocalData() {
    const mockData = {
        'sh000300': { name: '沪深300', price: 4469.22, change: 25.3, changePercent: 0.57 },
        'sh000016': { name: '上证50', price: 2890.15, change: 15.2, changePercent: 0.53 },
        'sh000905': { name: '中证500', price: 6951.80, change: 45.6, changePercent: 0.66 },
        'sh000688': { name: '科创50', price: 1085.32, change: -12.5, changePercent: -1.14 },
        'sz399006': { name: '创业板指', price: 2156.78, change: 18.3, changePercent: 0.85 },
        'sh000852': { name: '中证1000', price: 7856.42, change: 52.1, changePercent: 0.67 }
    };
    
    const result = [];
    for (const code in mockData) {
        const item = mockData[code];
        const peInfo = getLocalPEInfo(code);
        result.push({
            code,
            name: item.name,
            type: INDEX_CONFIG[code].type,
            risk: INDEX_CONFIG[code].risk,
            price: item.price,
            change: item.change,
            changePercent: item.changePercent,
            pe: peInfo.current,
            peMin: peInfo.min,
            peMax: peInfo.max,
            pePercentile: peInfo.percentile
        });
    }
    
    return {
        success: true,
        data: result,
        timestamp: new Date().toLocaleString('zh-CN')
    };
}

// 本地PE数据
function getLocalPEInfo(code) {
    const peData = {
        'sh000300': { current: 14.18, min: 10, max: 18 },
        'sh000016': { current: 11.5, min: 8, max: 15 },
        'sh000905': { current: 22.5, min: 15, max: 35 },
        'sh000688': { current: 65, min: 35, max: 85 },
        'sz399006': { current: 28, min: 25, max: 60 },
        'sh000852': { current: 32, min: 20, max: 50 }
    };
    
    const info = peData[code] || { current: 20, min: 10, max: 30 };
    const range = info.max - info.min;
    const position = info.current - info.min;
    const percentile = Math.round((position / range) * 100);
    
    return {
        current: info.current,
        min: info.min,
        max: info.max,
        percentile: percentile
    };
}

// 计算PE百分位
function calculatePEPercentile(code) {
    const peInfo = getLocalPEInfo(code);
    return peInfo.percentile;
}

// 计算综合评分
function calculateScore(item) {
    let score = 50;
    const pePercentile = item.pePercentile || 50;
    const risk = item.risk || '中';
    const changePercent = item.changePercent || 0;
    
    if (pePercentile < 20) score += 20;
    else if (pePercentile < 30) score += 15;
    else if (pePercentile < 40) score += 10;
    else if (pePercentile < 50) score += 5;
    else if (pePercentile > 80) score -= 15;
    else if (pePercentile > 70) score -= 10;
    else if (pePercentile > 60) score -= 5;
    
    if (changePercent > 2) score += 10;
    else if (changePercent > 0) score += 5;
    else if (changePercent < -2) score -= 5;
    
    if (risk === '低') score += 5;
    else if (risk === '高') score -= 3;
    
    return Math.max(0, Math.min(100, score));
}

// 获取定投建议
function getRecommendation(pePercentile) {
    if (pePercentile < 30) {
        return {
            text: '✅ 当前估值偏低，建议加倍定投',
            class: 'rec-buy',
            multiplier: 1.5,
            badge: 'badge-low',
            badgeText: '低估',
            action: 'buy-more',
            reason: 'PE处于历史低位，是积累筹码的好时机'
        };
    } else if (pePercentile < 70) {
        return {
            text: '➡️ 估值合理，建议正常定投',
            class: 'rec-hold',
            multiplier: 1.0,
            badge: 'badge-mid',
            badgeText: '合理',
            action: 'normal',
            reason: '估值处于合理区间，按计划执行即可'
        };
    } else {
        return {
            text: '⚠️ 估值偏高，建议减少定投或止盈',
            class: 'rec-sell',
            multiplier: 0.5,
            badge: 'badge-high',
            badgeText: '高估',
            action: 'reduce',
            reason: '估值处于高位，注意控制风险'
        };
    }
}

// 获取详细操作建议
function getDetailedAdvice(action) {
    const advices = {
        'buy-more': {
            title: '💚 积极定投期',
            steps: [
                '将定投金额提高至平时的1.5-2倍',
                '可一次性投入3-6个月的定投预算',
                '重点关注宽基指数（沪深300、中证500）',
                '设置止盈目标：年化10-15%'
            ],
            warning: '虽然估值偏低，但仍需分批投入，避免单次重仓',
            timeframe: '建议持续3-6个月'
        },
        'normal': {
            title: '💛 正常定投期',
            steps: [
                '按原计划执行定投，保持纪律',
                '每月固定日期投入固定金额',
                '可考虑定投日设置在每月下旬',
                '坚持长期持有，不轻易中断'
            ],
            warning: '避免追涨杀跌，保持投资纪律最重要',
            timeframe: '建议持续持有1年以上'
        },
        'reduce': {
            title: '❤️ 谨慎期/止盈期',
            steps: [
                '将定投金额减少至平时的0.5倍或暂停',
                '已达到止盈目标的，可分批卖出30-50%',
                '将资金暂时转入货币基金或债券基金',
                '等待估值回落后再恢复定投'
            ],
            warning: '不要一次性清仓，分批止盈更稳妥',
            timeframe: '建议观望1-3个月'
        }
    };
    
    return advices[action] || advices['normal'];
}

// 渲染指数卡片
function renderIndexCards(data) {
    const container = document.getElementById('indexCards');
    container.innerHTML = '';
    
    data.forEach(item => {
        const config = INDEX_CONFIG[item.code] || { name: item.name, type: '其他', risk: '中' };
        const pePercentile = item.pePercentile || calculatePEPercentile(item.code);
        const score = calculateScore(item);
        const recommendation = getRecommendation(pePercentile);
        
        const isUp = item.changePercent >= 0;
        const changeClass = isUp ? 'change-up' : 'change-down';
        const changeSymbol = isUp ? '+' : '';
        
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <div class="card-header">
                <div>
                    <div class="card-title">${config.name}</div>
                    <small style="color: var(--text-light);">${config.type} · 风险${config.risk}</small>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    ${item.source === 'simulated' ? '<span style="font-size: 0.7rem; background: #fef3c7; color: #92400e; padding: 2px 6px; border-radius: 4px;">模拟</span>' : '<span style="font-size: 0.7rem; background: #dcfce7; color: #166534; padding: 2px 6px; border-radius: 4px;">实时</span>'}
                    <span class="badge ${recommendation.badge}">${recommendation.badgeText}</span>
                </div>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div>
                    <div class="price">${item.price.toFixed(2)}</div>
                    <div class="change ${changeClass}">
                        ${changeSymbol}${item.changePercent.toFixed(2)}% 
                        (${changeSymbol}${item.change.toFixed(2)})
                    </div>
                </div>
                <div style="text-align: center; padding: 8px 16px; background: ${score >= 70 ? '#dcfce7' : score >= 50 ? '#fef3c7' : '#fee2e2'}; border-radius: 8px;">
                    <div style="font-size: 0.75rem; color: var(--text-light);">综合评分</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: ${score >= 70 ? '#166534' : score >= 50 ? '#92400e' : '#991b1b'};">${score}</div>
                </div>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">PE估值</div>
                    <div class="metric-value">${item.pe ? item.pe.toFixed(2) : '--'}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">历史分位</div>
                    <div class="metric-value">${pePercentile}%</div>
                </div>
            </div>
            
            <div class="pe-bar">
                <div class="pe-fill ${pePercentile < 30 ? 'low' : pePercentile < 70 ? 'mid' : 'high'}" 
                     style="width: ${pePercentile}%"></div>
            </div>
            <small style="color: var(--text-light); display: block; margin-top: 4px;">
                估值区间: ${item.peMin || '--'} - ${item.peMax || '--'}
            </small>
            
            <div class="recommendation ${recommendation.class}">
                <strong>定投建议:</strong> ${recommendation.text}
                <br><small>建议倍数: ${recommendation.multiplier}x · ${recommendation.reason}</small>
            </div>
            
            <div style="margin-top: 12px; padding: 10px; background: #f8fafc; border-radius: 8px; font-size: 0.85rem;">
                <strong>💡 适合人群:</strong> ${config.bestFor}
                <br><strong>📈 推荐基金:</strong> ${config.fundOptions[0]}
            </div>
        `;
        
        container.appendChild(card);
    });
    
    renderStockPickingAdvice(data);
    renderOperationAdvice(data);
    renderCharts(data);
}

// 渲染选股建议
function renderStockPickingAdvice(data) {
    const container = document.getElementById('stockPickingAdvice');
    if (!container) return;
    
    const scoredData = data.map(item => ({
        ...item,
        score: calculateScore(item),
        pePercentile: item.pePercentile || calculatePEPercentile(item.code)
    })).sort((a, b) => b.score - a.score);
    
    let html = '<div class="advice-list">';
    scoredData.forEach((rec, index) => {
        const priorityColor = rec.score >= 70 ? '#10b981' : rec.score >= 50 ? '#f59e0b' : '#ef4444';
        const priorityText = rec.score >= 70 ? '强烈推荐' : rec.score >= 50 ? '推荐' : '观望';
        const config = INDEX_CONFIG[rec.code] || {};
        
        html += `
            <div class="advice-item" style="border-left: 4px solid ${priorityColor}; padding: 16px; margin-bottom: 12px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div style="font-weight: 600; font-size: 1.1rem;">
                        ${index + 1}. ${rec.name}
                        <span style="background: ${priorityColor}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; margin-left: 8px;">${priorityText}</span>
                    </div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: ${priorityColor};">${rec.score}分</div>
                </div>
                <div style="color: var(--text-light); font-size: 0.9rem; margin-bottom: 8px;">
                    PE分位: ${rec.pePercentile}% | 风险等级: ${rec.risk}
                </div>
                <div style="font-size: 0.9rem; color: var(--text);">
                    ${rec.pePercentile < 30 ? `估值处于历史低位(${rec.pePercentile}%)，安全边际高，适合长期布局` : 
                      rec.pePercentile > 70 ? `估值偏高(${rec.pePercentile}%)，建议观望或减仓` :
                      `估值合理(${rec.pePercentile}%)，${config.description || ''}，适合稳健配置`}
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
}

// 渲染操作建议
function renderOperationAdvice(data) {
    const container = document.getElementById('operationAdvice');
    if (!container) return;
    
    const scoredData = data.map(item => ({
        ...item,
        score: calculateScore(item),
        pePercentile: item.pePercentile || calculatePEPercentile(item.code)
    })).sort((a, b) => b.score - a.score);
    
    const best = scoredData[0];
    if (!best) return;
    
    const config = INDEX_CONFIG[best.code] || {};
    const recommendation = getRecommendation(best.pePercentile);
    const detailedAdvice = getDetailedAdvice(recommendation.action);
    
    let html = `
        <div class="operation-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 16px; padding: 24px;">
            <h3 style="margin-bottom: 16px; font-size: 1.3rem;">${detailedAdvice.title}</h3>
            
            <div style="background: rgba(255,255,255,0.1); border-radius: 12px; padding: 16px; margin-bottom: 16px;">
                <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 8px;">当前重点关注</div>
                <div style="font-size: 1.5rem; font-weight: 700;">${best.name}</div>
                <div style="font-size: 0.9rem; opacity: 0.8; margin-top: 4px;">
                    评分: ${best.score}分 | PE分位: ${best.pePercentile}% | 建议: ${recommendation.multiplier}x定投
                </div>
            </div>
            
            <div style="margin-bottom: 16px;">
                <div style="font-weight: 600; margin-bottom: 8px;">📋 具体操作建议:</div>
                <ol style="padding-left: 20px; line-height: 1.8;">
                    ${detailedAdvice.steps.map(step => `<li>${step}</li>`).join('')}
                </ol>
            </div>
            
            <div style="background: rgba(255,255,255,0.15); border-radius: 8px; padding: 12px; margin-bottom: 12px;">
                <div style="font-weight: 600; margin-bottom: 4px;">⚠️ 风险提示:</div>
                <div style="font-size: 0.9rem; opacity: 0.9;">${detailedAdvice.warning}</div>
            </div>
            
            <div style="font-size: 0.9rem; opacity: 0.8;">
                <strong>⏱️ 时间建议:</strong> ${detailedAdvice.timeframe}
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// 生成历史数据
function generateHistoryData(data) {
    const days = 30;
    const dates = [];
    const peData = {};
    const priceData = {};
    const scoreData = {};
    
    const today = new Date();
    
    data.forEach(item => {
        peData[item.code] = [];
        priceData[item.code] = [];
        scoreData[item.code] = [];
    });
    
    for (let i = days - 1; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        dates.push(date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }));
        
        data.forEach(item => {
            const randomFactor = 0.98 + Math.random() * 0.04;
            const basePE = item.pe || 20;
            const basePrice = item.price;
            
            peData[item.code].push((basePE * randomFactor).toFixed(2));
            priceData[item.code].push((basePrice * randomFactor).toFixed(2));
            
            const pePercentile = item.pePercentile || calculatePEPercentile(item.code);
            const score = calculateScore({
                ...item,
                changePercent: (randomFactor - 1) * 100
            });
            scoreData[item.code].push(score);
        });
    }
    
    return { dates, peData, priceData, scoreData };
}

// 渲染图表
function renderCharts(data) {
    const history = generateHistoryData(data);
    
    const peCtx = document.getElementById('peChart');
    if (peCtx) {
        if (peChart) peChart.destroy();
        
        const peDatasets = data.map((item, index) => ({
            label: item.name,
            data: history.peData[item.code],
            borderColor: getColor(index),
            backgroundColor: getColor(index, 0.1),
            tension: 0.4,
            fill: false
        }));
        
        peChart = new Chart(peCtx, {
            type: 'line',
            data: {
                labels: history.dates,
                datasets: peDatasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    title: { display: true, text: 'PE估值走势（近30天）' }
                },
                scales: {
                    y: { beginAtZero: false }
                }
            }
        });
    }
    
    const priceCtx = document.getElementById('priceChart');
    if (priceCtx) {
        if (priceChart) priceChart.destroy();
        
        const priceDatasets = data.map((item, index) => ({
            label: item.name,
            data: history.priceData[item.code],
            borderColor: getColor(index),
            backgroundColor: getColor(index, 0.1),
            tension: 0.4,
            fill: false
        }));
        
        priceChart = new Chart(priceCtx, {
            type: 'line',
            data: {
                labels: history.dates,
                datasets: priceDatasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    title: { display: true, text: '价格指数走势（近30天）' }
                },
                scales: {
                    y: { beginAtZero: false }
                }
            }
        });
    }
    
    const scoreCtx = document.getElementById('scoreChart');
    if (scoreCtx) {
        if (scoreChart) scoreChart.destroy();
        
        const scoreDatasets = data.map((item, index) => ({
            label: item.name,
            data: history.scoreData[item.code],
            borderColor: getColor(index),
            backgroundColor: getColor(index, 0.1),
            tension: 0.4,
            fill: false
        }));
        
        scoreChart = new Chart(scoreCtx, {
            type: 'line',
            data: {
                labels: history.dates,
                datasets: scoreDatasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    title: { display: true, text: '综合评分趋势（近30天）' }
                },
                scales: {
                    y: { min: 0, max: 100 }
                }
            }
        });
    }
}

// 获取颜色
function getColor(index, alpha = 1) {
    const colors = [
        `rgba(79, 70, 229, ${alpha})`,
        `rgba(16, 185, 129, ${alpha})`,
        `rgba(245, 158, 11, ${alpha})`,
        `rgba(239, 68, 68, ${alpha})`,
        `rgba(99, 102, 241, ${alpha})`,
        `rgba(139, 92, 246, ${alpha})`
    ];
    return colors[index % colors.length];
}

// 切换标签页
function switchTab(element, tabName) {
    if (!element) return;
    
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    element.classList.add('active');
    const targetContent = document.getElementById(`tab-${tabName}`);
    if (targetContent) {
        targetContent.classList.add('active');
    }
}

// 切换提醒设置
function toggleAlert(type) {
    const idMap = { low: 'alertLow', high: 'alertHigh', monthly: 'alertMonthly' };
    const toggle = document.getElementById(idMap[type]);
    if (toggle) {
        toggle.classList.toggle('active');
    }
}

// 保存提醒设置 - 使用数据库
async function saveAlertSettings() {
    const peThreshold = parseInt(document.getElementById('peThreshold')?.value) || 30;
    const investDay = parseInt(document.getElementById('investDay')?.value) || 1;
    
    try {
        const result = await fetchFromAPI('/api/settings/alert', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pe_threshold: peThreshold,
                invest_day: investDay,
                enabled: 1
            })
        });
        
        if (result && result.success) {
            showMessage('✅ 提醒设置已保存到数据库！', 'success');
        } else {
            throw new Error(result.error || '保存失败');
        }
    } catch (e) {
        console.error('保存设置失败:', e);
        showMessage('保存失败：' + e.message, 'error');
    }
}

// 加载提醒设置 - 从数据库
async function loadAlertSettings() {
    try {
        const result = await fetchFromAPI('/api/settings/alert');
        
        if (result && result.success && result.settings) {
            const settings = result.settings;
            const peThresholdEl = document.getElementById('peThreshold');
            const investDayEl = document.getElementById('investDay');
            
            if (peThresholdEl && settings.pe_threshold) {
                peThresholdEl.value = settings.pe_threshold;
            }
            if (investDayEl && settings.invest_day) {
                investDayEl.value = settings.invest_day;
            }
        }
    } catch (e) {
        console.error('加载设置失败:', e);
    }
}

// 止盈止损提醒设置 - 使用数据库
async function saveStopSettings() {
    const stopProfit = parseFloat(document.getElementById('stopProfit').value) || 15;
    const stopLoss = parseFloat(document.getElementById('stopLoss').value) || -10;
    const benchmarkIndex = document.getElementById('benchmarkIndex').value;
    
    try {
        const result = await fetchFromAPI('/api/settings/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                index_code: benchmarkIndex,
                stop_profit: stopProfit,
                stop_loss: stopLoss
            })
        });
        
        if (result && result.success) {
            // 显示保存状态
            const statusEl = document.getElementById('stopAlertStatus');
            const contentEl = document.getElementById('stopAlertContent');
            if (statusEl && contentEl) {
                statusEl.style.display = 'block';
                contentEl.innerHTML = `
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <div>
                            <span style="color: #166534; font-weight: 600;">🎯 止盈线:</span>
                            <span>${stopProfit}%</span>
                        </div>
                        <div>
                            <span style="color: #991b1b; font-weight: 600;">🛑 止损线:</span>
                            <span>${stopLoss}%</span>
                        </div>
                        <div style="grid-column: 1 / -1;">
                            <span style="color: var(--text-light);">📊 基准:</span>
                            <span>${INDEX_CONFIG[benchmarkIndex]?.name || benchmarkIndex}</span>
                        </div>
                    </div>
                `;
            }
            
            showMessage('✅ 止盈止损设置已保存到数据库！', 'success');
            checkStopAlerts();
        } else {
            throw new Error(result.error || '保存失败');
        }
    } catch (e) {
        console.error('保存止盈止损设置失败:', e);
        showMessage('保存失败：' + e.message, 'error');
    }
}

// 加载止盈止损设置 - 从数据库
async function loadStopSettings() {
    try {
        const benchmarkIndex = document.getElementById('benchmarkIndex')?.value || 'sh000300';
        const result = await fetchFromAPI(`/api/settings/stop?index_code=${benchmarkIndex}`);
        
        if (result && result.success && result.settings) {
            const settings = result.settings;
            
            if (settings.stop_profit) document.getElementById('stopProfit').value = settings.stop_profit;
            if (settings.stop_loss) document.getElementById('stopLoss').value = settings.stop_loss;
            if (settings.index_code) document.getElementById('benchmarkIndex').value = settings.index_code;
            
            // 显示当前设置
            const statusEl = document.getElementById('stopAlertStatus');
            const contentEl = document.getElementById('stopAlertContent');
            if (statusEl && contentEl) {
                statusEl.style.display = 'block';
                contentEl.innerHTML = `
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <div>
                            <span style="color: #166534; font-weight: 600;">🎯 止盈线:</span>
                            <span>${settings.stop_profit}%</span>
                        </div>
                        <div>
                            <span style="color: #991b1b; font-weight: 600;">🛑 止损线:</span>
                            <span>${settings.stop_loss}%</span>
                        </div>
                        <div style="grid-column: 1 / -1;">
                            <span style="color: var(--text-light);">📊 基准:</span>
                            <span>${INDEX_CONFIG[settings.index_code]?.name || settings.index_code}</span>
                        </div>
                    </div>
                `;
            }
        }
    } catch (e) {
        console.error('加载止盈止损设置失败:', e);
    }
}

// 检查止盈止损提醒
async function checkStopAlerts() {
    try {
        // 获取止盈止损设置
        const benchmarkIndex = document.getElementById('benchmarkIndex')?.value || 'sh000300';
        const stopResult = await fetchFromAPI(`/api/settings/stop?index_code=${benchmarkIndex}`);
        const stopSettings = stopResult?.settings;
        
        if (!stopSettings) return;
        
        const stopProfit = stopSettings.stop_profit || 15;
        const stopLoss = stopSettings.stop_loss || -10;
        
        // 获取所有定投记录（带有买入点位）
        const recordsResult = await fetchFromAPI('/api/records');
        const records = recordsResult?.records || [];
        
        // 过滤有买入点位的记录
        const recordsWithPoints = records.filter(r => r.buy_index_point > 0);
        if (recordsWithPoints.length === 0) return;
        
        // 获取当前各指数价格
        const quotesResult = await fetchFromAPI('/api/quotes');
        if (!quotesResult || !quotesResult.data) return;
        
        const currentPrices = {};
        quotesResult.data.forEach(item => {
            currentPrices[item.code] = item.price;
        });
        
        // 检查每条记录的收益率
        recordsWithPoints.forEach(record => {
            const currentPrice = currentPrices[record.index_code];
            if (!currentPrice || !record.buy_index_point) return;
            
            // 计算收益率 = (当前点位 - 买入点位) / 买入点位 * 100
            const profitRate = ((currentPrice - record.buy_index_point) / record.buy_index_point) * 100;
            
            // 检查是否触发止盈
            if (profitRate >= stopProfit) {
                showStopAlert('profit', record, profitRate, stopProfit, currentPrice);
            }
            
            // 检查是否触发止损
            else if (profitRate <= stopLoss) {
                showStopAlert('loss', record, profitRate, stopLoss, currentPrice);
            }
        });
        
    } catch (e) {
        console.error('检查止盈止损提醒失败:', e);
    }
}

// 显示止盈止损提醒
function showStopAlert(type, record, currentRate, targetRate, currentPrice) {
    const alertId = `stop-alert-${record.id}`;
    if (document.getElementById(alertId)) return; // 避免重复显示
    
    const isProfit = type === 'profit';
    const bgColor = isProfit ? '#dcfce7' : '#fee2e2';
    const borderColor = isProfit ? '#166534' : '#991b1b';
    const icon = isProfit ? '🎯' : '🛑';
    const title = isProfit ? '止盈提醒' : '止损提醒';
    const message = isProfit 
        ? `${record.index_name} 已达到止盈目标！当前收益率 ${currentRate.toFixed(2)}%，建议分批卖出`
        : `${record.index_name} 已触发止损！当前收益率 ${currentRate.toFixed(2)}%，建议考虑止损或加仓摊薄成本`;
    
    const alertHtml = `
        <div id="${alertId}" style="
            position: fixed;
            top: 80px;
            right: 20px;
            width: 320px;
            background: ${bgColor};
            border: 2px solid ${borderColor};
            border-radius: 12px;
            padding: 16px;
            z-index: 10000;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease;
        ">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                <span style="font-size: 1.5rem;">${icon}</span>
                <span style="font-weight: 600; font-size: 1.1rem; color: ${borderColor};">${title}</span>
            </div>
            <p style="margin: 0 0 12px 0; color: #333; line-height: 1.5;">${message}</p>
            <div style="font-size: 0.85rem; color: #666; margin-bottom: 12px;">
                买入点位: ${record.buy_index_point?.toFixed(2) || 'N/A'} | 当前: ${currentPrice?.toFixed(2) || 'N/A'} | 买入日期: ${record.invest_date}
            </div>
            <button onclick="dismissStopAlert('${alertId}')" style="
                width: 100%;
                padding: 8px;
                background: ${borderColor};
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 500;
            ">我知道了</button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', alertHtml);
    
    // 5分钟后自动关闭
    setTimeout(() => {
        const el = document.getElementById(alertId);
        if (el) el.remove();
    }, 300000);
}

// 关闭止盈止损提醒
function dismissStopAlert(alertId) {
    const el = document.getElementById(alertId);
    if (el) el.remove();
}

// 显示消息提示
function showMessage(text, type = 'success') {
    const msg = document.createElement('div');
    msg.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: ${type === 'success' ? '#10b981' : '#ef4444'};
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        z-index: 10000;
        font-weight: 500;
        animation: fadeIn 0.3s ease;
    `;
    msg.textContent = text;
    document.body.appendChild(msg);
    
    setTimeout(() => {
        if (msg.parentNode) msg.parentNode.removeChild(msg);
    }, 2000);
}

// 页面加载完成后初始化 - 已合并到下方DOMContentLoaded
// (removed duplicate listener)

// 添加动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateX(-50%) translateY(-10px); }
        to { opacity: 1; transform: translateX(-50%) translateY(0); }
    }
`;
document.head.appendChild(style);

// 定投记录管理 - 使用数据库API
async function addRecord() {
    const indexCode = document.getElementById('recordIndex').value;
    const amount = parseFloat(document.getElementById('recordAmount').value);
    const indexPoint = parseFloat(document.getElementById('recordIndexPoint').value) || 0;
    const date = document.getElementById('recordDate').value;
    
    if (!date) {
        showMessage('请选择定投日期', 'error');
        return;
    }
    
    try {
        const result = await fetchFromAPI('/api/records', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                index_code: indexCode,
                index_name: INDEX_CONFIG[indexCode].name,
                amount: amount,
                invest_date: date,
                note: '',
                buy_price: amount,  // 买入金额
                buy_index_point: indexPoint  // 买入时指数点位
            })
        });
        
        if (result && result.success) {
            await renderRecords();
            await updateStats();
            
            document.getElementById('recordAmount').value = '1000';
            document.getElementById('recordIndexPoint').value = '0';
            document.getElementById('recordDate').value = '';
            
            showMessage('✅ 记录添加成功！', 'success');
        } else {
            throw new Error(result.error || '添加失败');
        }
    } catch (e) {
        console.error('添加记录失败:', e);
        showMessage('添加失败：' + e.message, 'error');
    }
}

// 删除记录
async function deleteRecord(id) {
    try {
        const result = await fetchFromAPI(`/api/records/${id}`, {
            method: 'DELETE'
        });
        
        if (result && result.success) {
            await renderRecords();
            await updateStats();
            showMessage('记录已删除', 'success');
        } else {
            throw new Error(result.error || '删除失败');
        }
    } catch (e) {
        console.error('删除记录失败:', e);
        showMessage('删除失败：' + e.message, 'error');
    }
}

// 渲染记录列表 - 从数据库获取
async function renderRecords() {
    const container = document.getElementById('recordList');
    if (!container) return;
    
    try {
        const result = await fetchFromAPI('/api/records');
        
        if (!result || !result.success) {
            container.innerHTML = '<div class="record-empty">加载失败，请刷新重试</div>';
            return;
        }
        
        const records = result.records || [];
        
        if (records.length === 0) {
            container.innerHTML = '<div class="record-empty">暂无定投记录，点击上方按钮添加</div>';
            return;
        }
        
        let html = '';
        records.forEach(record => {
            html += `
                <div class="record-item">
                    <div>
                        <div style="font-weight: 600;">${record.index_name}</div>
                        <div style="font-size: 0.85rem; color: var(--text-light);">${record.invest_date}</div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 16px;">
                        <div style="font-size: 1.2rem; font-weight: 700; color: var(--primary);">¥${record.amount.toLocaleString()}</div>
                        <button class="btn btn-danger" onclick="deleteRecord(${record.id})">删除</button>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    } catch (e) {
        console.error('渲染记录失败:', e);
        container.innerHTML = '<div class="record-empty">加载失败，请刷新重试</div>';
    }
}

// 更新统计数据 - 从数据库获取
async function updateStats() {
    try {
        const result = await fetchFromAPI('/api/stats');
        
        if (!result || !result.success) {
            return;
        }
        
        const stats = result.stats;
        
        const el1 = document.getElementById('statTotalInvest');
        const el2 = document.getElementById('statTotalTimes');
        const el3 = document.getElementById('statAvgAmount');
        const el4 = document.getElementById('statLastInvest');
        
        if (el1) el1.textContent = `¥${Math.round(stats.total_amount || 0).toLocaleString()}`;
        if (el2) el2.textContent = `${stats.total_times || 0}次`;
        if (el3) el3.textContent = `¥${Math.round(stats.avg_amount || 0).toLocaleString()}`;
        if (el4) el4.textContent = stats.last_date || '--';
        
    } catch (e) {
        console.error('更新统计失败:', e);
    }
}

// 导出记录
async function exportRecords() {
    try {
        const result = await fetchFromAPI('/api/records');
        
        if (!result || !result.success || result.records.length === 0) {
            showMessage('暂无记录可导出', 'error');
            return;
        }
        
        const records = result.records;
        let csv = '\uFEFF日期,指数,金额\n';
        records.forEach(r => {
            csv += `${r.invest_date},${r.index_name},${r.amount}\n`;
        });
        
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `定投记录_${new Date().toLocaleDateString()}.csv`;
        link.click();
        
        showMessage('✅ 导出成功！', 'success');
    } catch (e) {
        console.error('导出失败:', e);
        showMessage('导出失败，请重试', 'error');
    }
}

// ========== 云端备份功能 ==========

// 创建云端备份
async function createCloudBackup() {
    const btn = document.querySelector('button[onclick="createCloudBackup()"]');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="spinner" style="width: 16px; height: 16px; border-width: 2px; display: inline-block; vertical-align: middle; margin-right: 4px;"></span> 备份中...';
    btn.disabled = true;
    
    try {
        // 从数据库获取数据
        const recordsResult = await fetchFromAPI('/api/records');
        const alertResult = await fetchFromAPI('/api/settings/alert');
        const benchmarkIndex = document.getElementById('benchmarkIndex')?.value || 'sh000300';
        const stopResult = await fetchFromAPI(`/api/settings/stop?index_code=${benchmarkIndex}`);
        
        const records = recordsResult?.records || [];
        const alertSettings = alertResult?.settings || {};
        const stopSettings = stopResult?.settings || {};
        
        if (records.length === 0 && Object.keys(alertSettings).length === 0 && Object.keys(stopSettings).length === 0) {
            showMessage('没有数据需要备份', 'error');
            return;
        }
        
        const backupData = {
            records: records,
            settings: {
                alert: alertSettings,
                stop: stopSettings
            }
        };
        
        const result = await fetchFromAPI('/api/backup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(backupData)
        });
        
        if (result && result.success) {
            // 显示备份码
            document.getElementById('backupCode').textContent = result.backup_code;
            document.getElementById('backupResult').style.display = 'block';
            showMessage(`✅ 备份成功！备份码：${result.backup_code}`, 'success');
            
            // 保存备份码到本地记录
            let backupCodes = JSON.parse(localStorage.getItem('fundDCA_backupCodes') || '[]');
            backupCodes.unshift({
                code: result.backup_code,
                date: result.created_at,
                count: result.records_count || records.length
            });
            localStorage.setItem('fundDCA_backupCodes', JSON.stringify(backupCodes.slice(0, 10))); // 只保留最近10个
        } else {
            throw new Error(result.error || '备份失败');
        }
    } catch (error) {
        console.error('备份失败:', error);
        showMessage('备份失败：' + error.message, 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// 从云端恢复
async function restoreFromCloud() {
    const codeInput = document.getElementById('restoreCode');
    const code = codeInput.value.trim().toUpperCase();
    const resultDiv = document.getElementById('restoreResult');
    
    if (!code || code.length !== 6) {
        resultDiv.innerHTML = '<div style="color: #fee2e2;">请输入6位备份码</div>';
        resultDiv.style.display = 'block';
        return;
    }
    
    const btn = document.querySelector('button[onclick="restoreFromCloud()"]');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="spinner" style="width: 16px; height: 16px; border-width: 2px; display: inline-block; vertical-align: middle; margin-right: 4px;"></span> 恢复中...';
    btn.disabled = true;
    
    try {
        const result = await fetchFromAPI(`/api/backup/${code}`);
        
        if (result && result.success) {
            // 确认是否覆盖
            const currentRecords = JSON.parse(localStorage.getItem('fundDCA_records') || '[]');
            let confirmMsg = `找到备份数据：\n`;
            confirmMsg += `• 创建时间：${result.created_at}\n`;
            confirmMsg += `• 记录数量：${result.records_count} 条\n`;
            if (currentRecords.length > 0) {
                confirmMsg += `\n⚠️ 当前有 ${currentRecords.length} 条本地记录，恢复后将覆盖！\n`;
            }
            confirmMsg += `\n确定要恢复吗？`;
            
            if (confirm(confirmMsg)) {
                // 恢复数据
                localStorage.setItem('fundDCA_records', JSON.stringify(result.records));
                
                if (result.settings) {
                    if (result.settings.alert) {
                        localStorage.setItem('fundDCA_alertSettings', JSON.stringify(result.settings.alert));
                    }
                    if (result.settings.stop) {
                        localStorage.setItem('fundDCA_stopSettings', JSON.stringify(result.settings.stop));
                    }
                }
                
                // 刷新页面显示
                renderRecords();
                updateStats();
                loadAlertSettings();
                loadStopSettings();
                
                resultDiv.innerHTML = `
                    <div style="background: rgba(255,255,255,0.2); padding: 12px; border-radius: 8px;">
                        <div style="font-weight: 600; margin-bottom: 4px;">✅ 恢复成功！</div>
                        <div style="font-size: 0.9rem;">已恢复 ${result.records_count} 条定投记录</div>
                    </div>
                `;
                resultDiv.style.display = 'block';
                codeInput.value = '';
                
                showMessage('✅ 数据恢复成功！', 'success');
            }
        } else {
            resultDiv.innerHTML = `<div style="color: #fee2e2;">❌ ${result.error || '备份码不存在'}</div>`;
            resultDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('恢复失败:', error);
        resultDiv.innerHTML = `<div style="color: #fee2e2;">❌ 恢复失败：${error.message}</div>`;
        resultDiv.style.display = 'block';
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// 显示消息
function showMessage(text, type) {
    const msg = document.createElement('div');
    msg.style.cssText = `position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: ${type === 'success' ? '#10b981' : '#ef4444'}; color: white; padding: 12px 24px; border-radius: 8px; z-index: 10000; font-weight: 500;`;
    msg.textContent = text;
    document.body.appendChild(msg);
    
    setTimeout(() => {
        if (msg.parentNode) {
            msg.parentNode.removeChild(msg);
        }
    }, 2000);
}

// 初始化数据
async function initData() {
    const updateTimeEl = document.getElementById('updateTime');
    const dataSourceEl = document.getElementById('dataSource');
    const container = document.getElementById('indexCards');
    
    // 显示骨架屏
    container.innerHTML = `
        <div class="skeleton-card">
            <div class="skeleton-line w-60"></div>
            <div class="skeleton-line w-40"></div>
            <div class="skeleton-block" style="height: 60px; margin: 16px 0;"></div>
            <div class="skeleton-line w-100"></div>
            <div class="skeleton-line w-80"></div>
            <div class="skeleton-line w-60"></div>
        </div>
        <div class="skeleton-card">
            <div class="skeleton-line w-60"></div>
            <div class="skeleton-line w-40"></div>
            <div class="skeleton-block" style="height: 60px; margin: 16px 0;"></div>
            <div class="skeleton-line w-100"></div>
            <div class="skeleton-line w-80"></div>
            <div class="skeleton-line w-60"></div>
        </div>
        <div class="skeleton-card">
            <div class="skeleton-line w-60"></div>
            <div class="skeleton-line w-40"></div>
            <div class="skeleton-block" style="height: 60px; margin: 16px 0;"></div>
            <div class="skeleton-line w-100"></div>
            <div class="skeleton-line w-80"></div>
            <div class="skeleton-line w-60"></div>
        </div>
    `;
    
    try {
        // 显示加载状态
        if (updateTimeEl) {
            updateTimeEl.innerHTML = '<span style="color: #4f46e5;">⏳ 正在加载...</span>';
        }
        if (dataSourceEl) {
            dataSourceEl.textContent = '获取中...';
        }
        
        const result = await fetchQuotes();
        console.log('[initData] fetchQuotes返回:', JSON.stringify(result)?.substring(0, 200));
        
        if (result && result.success && result.data && result.data.length > 0) {
            renderIndexCards(result.data);
            
            // 更新数据来源
            if (dataSourceEl) {
                const sourceMap = {
                    'sina': '新浪财经',
                    'qq': '腾讯财经',
                    'sina_int': '新浪国际',
                    'simulated': '模拟数据',
                    'mixed': '新浪+腾讯',
                    'mock': '模拟数据'
                };
                const sourceName = sourceMap[result.source] || result.source || '后端API';
                dataSourceEl.textContent = sourceName;
            }
            
            // 更新更新时间
            if (updateTimeEl) {
                updateTimeEl.textContent = result.timestamp || new Date().toLocaleString('zh-CN');
            }
            
            // 检查止盈止损提醒
            setTimeout(() => checkStopAlerts(), 1000);
        } else {
            throw new Error('API返回数据无效');
        }
    } catch (error) {
        console.error('初始化数据失败:', error);
        
        if (updateTimeEl) {
            updateTimeEl.textContent = new Date().toLocaleString('zh-CN');
        }
        if (dataSourceEl) {
            dataSourceEl.textContent = '加载失败，请点击刷新';
        }
        
        // 显示错误提示，而不是降级到旧数据
        const container = document.getElementById('indexCards');
        if (container) {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-light);">
                    <div style="font-size: 2rem; margin-bottom: 12px;">⚠️</div>
                    <div style="font-weight: 600; margin-bottom: 8px;">数据加载失败</div>
                    <div style="font-size: 0.9rem; margin-bottom: 16px;">请检查网络连接后点击刷新</div>
                    <button class="btn" onclick="refreshAllData()" style="margin: 0 auto;">🔄 重新加载</button>
                </div>
            `;
        }
    }
}

// 刷新所有数据
async function refreshAllData() {
    const btn = document.querySelector('button[onclick="refreshAllData()"]');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner" style="width: 16px; height: 16px; border-width: 2px; display: inline-block; vertical-align: middle; margin-right: 4px;"></span> 刷新中...';
    }
    
    try {
        // 清除缓存并重新获取
        if (USE_API) {
            await fetchFromAPI('/api/quotes?_=' + Date.now());
        }
        
        // 重新初始化数据
        await initData();
        
        // 重新加载历史图表
        if (typeof loadHistoryChart === 'function') {
            loadHistoryChart();
        }
        
        // 重新加载历史摘要
        if (typeof loadHistorySummary === 'function') {
            loadHistorySummary();
        }
    } catch (error) {
        console.error('刷新数据失败:', error);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '🔄 刷新数据';
        }
    }
}

// 定投收益计算器
function calculateDCA() {
    const monthlyAmount = parseFloat(document.getElementById('monthlyAmount').value) || 1000;
    const years = parseInt(document.getElementById('years').value) || 5;
    const annualReturn = parseFloat(document.getElementById('annualReturn').value) || 8;
    const strategyType = document.getElementById('strategyType').value;
    
    let adjustedReturn = annualReturn;
    switch(strategyType) {
        case 'conservative': adjustedReturn = 7.5; break;
        case 'balanced': adjustedReturn = 10; break;
        case 'aggressive': adjustedReturn = 12.5; break;
    }
    
    const months = years * 12;
    const monthlyReturn = adjustedReturn / 100 / 12;
    
    const totalPrincipal = monthlyAmount * months;
    const totalAsset = monthlyAmount * (Math.pow(1 + monthlyReturn, months) - 1) / monthlyReturn * (1 + monthlyReturn);
    const totalProfit = totalAsset - totalPrincipal;
    const profitPercent = (totalProfit / totalPrincipal * 100).toFixed(2);
    
    const el1 = document.getElementById('totalPrincipal');
    const el2 = document.getElementById('totalAsset');
    const el3 = document.getElementById('totalProfit');
    const el4 = document.getElementById('calcResult');
    
    if (el1) el1.textContent = `¥${totalPrincipal.toLocaleString('zh-CN', {maximumFractionDigits: 0})}`;
    if (el2) el2.textContent = `¥${totalAsset.toLocaleString('zh-CN', {maximumFractionDigits: 0})}`;
    if (el3) el3.textContent = `¥${totalProfit.toLocaleString('zh-CN', {maximumFractionDigits: 0})} (${profitPercent}%)`;
    if (el4) el4.classList.add('show');
}

// 自动刷新策略选择
function autoSelectStrategy() {
    const strategySelect = document.getElementById('strategyType');
    if (strategySelect) {
        strategySelect.addEventListener('change', function() {
            const returns = {
                'conservative': 7.5,
                'balanced': 10,
                'aggressive': 12.5
            };
            const annualEl = document.getElementById('annualReturn');
            if (annualEl) annualEl.value = returns[this.value];
        });
    }
}

// ============== 历史数据功能 ==============

let peBandChart = null;
let currentHistoryData = null;

// 加载历史数据图表
async function loadHistoryChart() {
    const code = document.getElementById('historyIndexSelect').value;
    const infoEl = document.getElementById('historyInfo');
    
    console.log(`[loadHistoryChart] 开始加载 ${code} 历史数据...`);
    
    if (infoEl) {
        infoEl.textContent = '⏳ 正在加载历史数据...';
        infoEl.style.color = '#4f46e5';
    }
    
    // 先尝试从API获取
    if (USE_API) {
        try {
            console.log(`[loadHistoryChart] 调用API: ${API_BASE_URL}/api/history/${code}`);
            const result = await fetchFromAPI(`/api/history/${code}`);
            console.log(`[loadHistoryChart] API返回:`, result ? `success=${result.success}, days=${result.totalDays}` : 'null');
            
            if (result && result.success && result.data && result.data.length > 0) {
                currentHistoryData = result.data;
                
                if (infoEl) {
                    infoEl.textContent = `✅ 共 ${result.totalDays} 个交易日 | 数据从 ${result.startDate} 至今`;
                    infoEl.style.color = '#10b981';
                }
                
                renderHistoryCharts(result.data, result.name);
                return;
            } else {
                console.log(`[loadHistoryChart] API返回数据无效:`, result);
            }
        } catch (e) {
            console.error('[loadHistoryChart] API调用失败:', e.message);
        }
    }
    
    // API失败，使用本地数据
    console.log('[loadHistoryChart] 切换到本地模拟数据');
    
    if (infoEl) {
        infoEl.textContent = '⚠️ 使用本地模拟数据（API连接失败）';
        infoEl.style.color = '#f59e0b';
    }
    
    // 使用本地模拟数据
    const mockData = generateLocalHistoryData(code);
    renderHistoryCharts(mockData, INDEX_CONFIG[code].name);
}

// 生成本地模拟历史数据
function generateLocalHistoryData(code) {
    const startDate = new Date('2010-01-01');
    const endDate = new Date();
    const data = [];
    
    const basePrices = {
        'sh000300': 3500, 'sh000016': 2500, 'sh000905': 6000,
        'sh000688': 1000, 'sz399006': 2000, 'sh000852': 7000
    };
    
    const basePE = {
        'sh000300': 13.5, 'sh000016': 11, 'sh000905': 25,
        'sh000688': 60, 'sz399006': 42, 'sh000852': 35
    };
    
    let current = new Date(startDate);
    let price = basePrices[code] || 3000;
    
    while (current <= endDate) {
        if (current.getDay() !== 0 && current.getDay() !== 6) {
            // 模拟价格波动
            const change = (Math.random() - 0.48) * 0.02;
            price = price * (1 + change);
            
            // 模拟PE波动
            const pe = basePE[code] * (1 + (Math.random() - 0.5) * 0.3);
            
            data.push({
                date: current.toISOString().split('T')[0],
                close: price,
                pe: pe,
                pePercentile: Math.random() * 100
            });
        }
        current.setDate(current.getDate() + 1);
    }
    
    return data;
}

// 渲染历史图表
function renderHistoryCharts(data, name) {
    // 数据采样（如果数据点太多）
    let chartData = data;
    if (data.length > 500) {
        const step = Math.floor(data.length / 500);
        chartData = data.filter((_, index) => index % step === 0);
    }
    
    const dates = chartData.map(d => d.date);
    const prices = chartData.map(d => d.close);
    const pes = chartData.map(d => d.pe);
    
    // PE估值走势图
    const peCtx = document.getElementById('peChart');
    if (peCtx) {
        if (peChart) peChart.destroy();
        
        peChart = new Chart(peCtx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: `${name} PE估值`,
                    data: pes,
                    borderColor: '#4f46e5',
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: true, text: `${name} PE估值走势（创立以来）` },
                    legend: { display: true }
                },
                scales: {
                    x: { display: false },
                    y: { 
                        beginAtZero: false,
                        title: { display: true, text: 'PE估值' }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }
    
    // 价格指数走势图（默认显示，更突出）
    const priceCtx = document.getElementById('priceChart');
    if (priceCtx) {
        if (priceChart) priceChart.destroy();
        
        // 计算涨跌幅
        const startPrice = prices[0];
        const endPrice = prices[prices.length - 1];
        const totalReturn = ((endPrice - startPrice) / startPrice * 100).toFixed(2);
        const isPositive = totalReturn >= 0;
        
        // 将日期转换为年份格式用于显示
        const yearLabels = dates.map(dateStr => {
            const date = new Date(dateStr);
            return date.getFullYear() + '年';
        });
        
        // 去重并保留年份标签
        const uniqueYears = [];
        let lastYear = '';
        yearLabels.forEach((year, index) => {
            if (year !== lastYear) {
                uniqueYears.push({ year, index });
                lastYear = year;
            }
        });
        
        // 生成用于显示的labels（只在年份变化时显示）
        const displayLabels = dates.map((dateStr, index) => {
            const date = new Date(dateStr);
            const year = date.getFullYear();
            // 只在每年的第一个数据点显示年份
            if (index === 0 || year !== new Date(dates[index - 1]).getFullYear()) {
                return year + '年';
            }
            return '';
        });
        
        priceChart = new Chart(priceCtx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: `${name} 价格指数`,
                    data: prices,
                    borderColor: isPositive ? '#10b981' : '#ef4444',
                    backgroundColor: isPositive ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                    borderWidth: 2.5,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { 
                        display: true, 
                        text: `${name} 价格指数走势（创立以来） | 累计收益: ${isPositive ? '+' : ''}${totalReturn}%`,
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: { display: false },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            title: function(context) {
                                const date = new Date(context[0].label);
                                return date.getFullYear() + '年' + (date.getMonth() + 1) + '月';
                            },
                            label: function(context) {
                                return `指数点位: ${context.parsed.y.toFixed(2)}点`;
                            }
                        }
                    }
                },
                scales: {
                    x: { 
                        display: true,
                        title: {
                            display: true,
                            text: '年份',
                            font: { weight: 'bold', size: 14 }
                        },
                        ticks: {
                            callback: function(val, index) {
                                // 只显示年份标签
                                const date = new Date(this.getLabelForValue(val));
                                const year = date.getFullYear();
                                // 每2-3年显示一个标签，避免拥挤
                                if (index === 0) return year + '年';
                                const prevDate = new Date(dates[index - 1]);
                                if (year !== prevDate.getFullYear()) {
                                    return year + '年';
                                }
                                return '';
                            },
                            maxRotation: 0,
                            autoSkip: false
                        }
                    },
                    y: { 
                        beginAtZero: false,
                        title: { 
                            display: true, 
                            text: '指数点数',
                            font: { weight: 'bold', size: 14 }
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(0) + '点';
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }
    
    // PE估值带图
    const peBandCtx = document.getElementById('peBandChart');
    if (peBandCtx) {
        if (peBandChart) peBandChart.destroy();
        
        // 计算PE分位数区间
        const sortedPE = [...pes].sort((a, b) => a - b);
        const pe10 = sortedPE[Math.floor(sortedPE.length * 0.1)];
        const pe30 = sortedPE[Math.floor(sortedPE.length * 0.3)];
        const pe50 = sortedPE[Math.floor(sortedPE.length * 0.5)];
        const pe70 = sortedPE[Math.floor(sortedPE.length * 0.7)];
        const pe90 = sortedPE[Math.floor(sortedPE.length * 0.9)];
        
        peBandCtx.height = 400;
        peBandChart = new Chart(peBandCtx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'PE估值',
                        data: pes,
                        borderColor: '#4f46e5',
                        backgroundColor: 'rgba(79, 70, 229, 0.1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.1,
                        fill: false
                    },
                    {
                        label: '90%分位（高估）',
                        data: new Array(dates.length).fill(pe90),
                        borderColor: '#ef4444',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        label: '70%分位',
                        data: new Array(dates.length).fill(pe70),
                        borderColor: '#f59e0b',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        label: '中位数',
                        data: new Array(dates.length).fill(pe50),
                        borderColor: '#6b7280',
                        borderWidth: 1,
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        label: '30%分位',
                        data: new Array(dates.length).fill(pe30),
                        borderColor: '#10b981',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        label: '10%分位（低估）',
                        data: new Array(dates.length).fill(pe10),
                        borderColor: '#059669',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { 
                        display: true, 
                        text: `${name} PE估值带（创立以来）` 
                    },
                    legend: { 
                        display: true,
                        position: 'bottom'
                    }
                },
                scales: {
                    x: { display: false },
                    y: { 
                        beginAtZero: false,
                        title: { display: true, text: 'PE估值' }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }
}

// 加载历史数据摘要
async function loadHistorySummary() {
    const container = document.getElementById('historySummary');
    if (!container) return;
    
    console.log('[loadHistorySummary] 开始加载历史数据摘要...');
    
    try {
        console.log(`[loadHistorySummary] 调用API: ${API_BASE_URL}/api/history/summary`);
        const result = await fetchFromAPI('/api/history/summary');
        console.log('[loadHistorySummary] API返回:', result ? `success=${result.success}, count=${result.data?.length}` : 'null');
        
        if (result && result.success && result.data && result.data.length > 0) {
            let html = '';
            result.data.forEach(item => {
                const statusColor = item.currentPercentile < 30 ? '#10b981' : 
                                   item.currentPercentile > 70 ? '#ef4444' : '#f59e0b';
                const statusText = item.currentPercentile < 30 ? '低估' : 
                                  item.currentPercentile > 70 ? '高估' : '合理';
                
                html += `
                    <div class="card" style="border-left: 4px solid ${statusColor};">
                        <div class="card-header">
                            <div>
                                <div class="card-title">${item.name}</div>
                                <small style="color: var(--text-light);">始于 ${item.startDate}</small>
                            </div>
                            <span class="badge" style="background: ${statusColor}; color: white;">${statusText}</span>
                        </div>
                        <div class="metrics" style="grid-template-columns: repeat(3, 1fr);">
                            <div class="metric">
                                <div class="metric-label">当前PE</div>
                                <div class="metric-value">${item.latestPE.toFixed(2)}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">PE分位</div>
                                <div class="metric-value" style="color: ${statusColor};">${item.currentPercentile.toFixed(1)}%</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">历史平均</div>
                                <div class="metric-value">${item.avgPE.toFixed(2)}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">PE区间</div>
                                <div class="metric-value">${item.minPE.toFixed(1)}-${item.maxPE.toFixed(1)}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">当前价格</div>
                                <div class="metric-value">${item.latestPrice.toFixed(2)}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">数据天数</div>
                                <div class="metric-value">${item.totalDays}</div>
                            </div>
                        </div>
                    </div>
                `;
            });
            container.innerHTML = html;
            console.log('[loadHistorySummary] 成功渲染摘要');
        } else {
            console.error('[loadHistorySummary] API返回数据无效:', result);
            container.innerHTML = '<div class="error">加载历史数据摘要失败</div>';
        }
    } catch (error) {
        console.error('[loadHistorySummary] 加载失败:', error);
        container.innerHTML = '<div class="error">加载失败</div>';
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 设置默认日期为今天
    const today = new Date().toISOString().split('T')[0];
    const dateEl = document.getElementById('recordDate');
    if (dateEl) dateEl.value = today;
    
    // 初始化数据
    initData();
    
    // 加载设置
    loadAlertSettings();
    loadStopSettings();
    
    // 加载定投记录
    renderRecords();
    updateStats();
    
    // 加载历史数据
    loadHistoryChart();
    loadHistorySummary();
    
    // 自动选择策略
    autoSelectStrategy();
    
    // 更新页面标题
    document.title = '指数基金定投助手';
    
    // 每30秒自动刷新数据
    setInterval(initData, 30000);
});

// 导出函数供全局使用
window.calculateDCA = calculateDCA;
window.switchTab = switchTab;
window.toggleAlert = toggleAlert;
window.saveAlertSettings = saveAlertSettings;
window.addRecord = addRecord;
window.deleteRecord = deleteRecord;
window.exportRecords = exportRecords;
window.loadHistoryChart = loadHistoryChart;
