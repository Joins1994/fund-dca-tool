# 指数基金定投助手 - 后端API服务

## 项目简介
这是一个基于Flask的指数基金数据API服务，提供实时行情、历史估值等数据。

## 功能特性
- 📊 实时指数行情
- 📈 历史PE估值数据
- 🔄 数据自动缓存
- 🌐 支持跨域请求

## 安装依赖

```bash
pip install flask flask-cors requests pandas
```

## 启动服务

```bash
python app.py
```

服务将在 http://localhost:5000 启动

## API接口

### 1. 获取指数实时行情
```
GET /api/quotes
```
返回示例：
```json
{
  "success": true,
  "data": [
    {
      "code": "sh000300",
      "name": "沪深300",
      "price": 4469.22,
      "change": 25.3,
      "changePercent": 0.57,
      "volume": 123456789,
      "amount": 9876543210
    }
  ],
  "timestamp": "2025-01-15 10:30:00"
}
```

### 2. 获取指数详情
```
GET /api/quote/<code>
```
参数：`code` - 指数代码，如 `sh000300`

### 3. 获取历史估值
```
GET /api/valuation/history/<code>
```
参数：`code` - 指数代码

### 4. 获取当前估值
```
GET /api/valuation/current/<code>
```
参数：`code` - 指数代码

### 5. 获取所有指数评分
```
GET /api/scores
```

### 6. 获取推荐定投方案
```
GET /api/recommendations
```

## 技术栈
- Python 3.8+
- Flask - Web框架
- Flask-CORS - 跨域支持
- Requests - HTTP请求
- Pandas - 数据处理

## 数据来源
- 新浪财经 - 实时行情
- 东方财富 - 估值数据
- 中证指数 - 指数信息

## 注意事项
⚠️ 本工具仅供参考学习，不构成投资建议
⚠️ 数据可能存在延迟，请以实际交易为准
⚠️ 请遵守各数据源的使用条款
