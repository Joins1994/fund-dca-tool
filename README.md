# 📈 指数基金定投助手

智能分析指数估值，提供定投建议的 Web 应用。

**在线访问**: http://101.37.70.202:5000

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)

## ✨ 功能

- 📊 **实时估值** - 沪深300、标普500等指数PE估值分析
- 📝 **定投记录** - 记录每次定投，自动计算收益
- 🔔 **止盈止损** - 自定义提醒阈值
- 📈 **历史走势** - 查看指数创立以来的长期趋势

## 🚀 快速开始

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

访问 http://localhost:5000

## 🛠️ 技术栈

- **后端**: Flask + SQLite
- **前端**: 原生 JavaScript + Chart.js
- **数据源**: 新浪财经、腾讯财经、Yahoo Finance

## 📁 目录结构

```
backend/
├── app.py           # Flask 应用
├── database.py      # 数据库模块
├── history_data.py  # 历史数据获取
├── static/          # 前端资源
└── templates/       # HTML 模板
```

## 📄 许可证

MIT

---

如果觉得有用，请给个 ⭐️
