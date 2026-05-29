# 📈 指数基金定投助手

> 智能分析指数估值，提供定投建议，支持止盈止损提醒

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Stars](https://img.shields.io/github/stars/Joins1994/fund-dca-tool)

## 🎯 功能特性

### 1. 实时指数数据
- 支持沪深300、上证50、中证500、科创50、创业板指、中证1000等A股指数
- 支持纳斯达克100、标普500等美股指数
- 支持恒生指数、日经225、德国DAX等海外指数
- 数据来源：新浪财经、腾讯财经（实时数据）

### 2. 智能估值分析
- PE估值百分位计算
- 历史估值区间展示
- 综合评分系统（0-100分）
- 估值建议（低估/合理/高估）

### 3. 定投记录管理
- 添加/删除定投记录
- 记录买入点位和金额
- 导出Excel格式
- SQLite本地存储

### 4. 止盈止损提醒
- 自定义止盈止损阈值
- 根据买入点位自动计算收益率
- 实时检测并弹出提醒

### 5. 历史走势查看
- 创立以来的长期历史走势
- 支持切换不同指数查看
- 指数历史数据摘要

## 🚀 在线演示

**已部署地址**: http://101.37.70.202:5000

## 🚀 快速开始

### 环境要求
- Python 3.8+
- pip

### 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 启动服务

```bash
python app.py
```

服务启动后访问：http://localhost:5000

## 📁 项目结构

```
fund-dca-tool/
├── backend/
│   ├── app.py              # Flask 主应用
│   ├── database.py         # SQLite 数据库模块
│   ├── history_data.py     # 历史数据模块
│   ├── requirements.txt     # Python 依赖
│   ├── fund_dca.db         # SQLite 数据库文件
│   ├── static/
│   │   └── app.js          # 前端 JavaScript
│   └── templates/
│       └── index.html      # 前端页面
├── .gitignore
└── README.md
```

## 🛠️ 技术栈

### 后端
- **Flask** - Web 框架
- **SQLite** - 本地数据库
- **Requests** - HTTP 请求库

### 前端
- **Chart.js** - 图表库
- **原生 JavaScript** - 无框架依赖
- **CSS3** - 响应式设计

### 数据源
- 新浪财经（A股数据）
- 腾讯财经（海外指数）
- 新浪国际（欧洲、日本指数）

## 📊 使用指南

### 添加定投记录
1. 选择指数品种
2. 输入定投金额
3. 填写买入时指数点位（可选）
4. 选择定投日期
5. 点击"添加记录"

### 设置止盈止损
1. 向下滚动到"止盈止损提醒设置"
2. 设置止盈阈值（如：20%）
3. 设置止损阈值（如：-10%）
4. 选择监控的指数
5. 点击"保存止盈止损设置"

### 查看历史走势
1. 选择想查看的指数
2. 系统自动加载创立以来的历史数据
3. 图表支持缩放和悬停查看详情

## 🔧 配置说明

### 修改端口
在 `backend/app.py` 中修改：
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### 数据库位置
数据库文件默认位置：`backend/fund_dca.db`

## 📝 TODO

- [ ] 添加用户认证系统
- [ ] 支持更多海外指数
- [ ] 添加定投收益率计算器
- [ ] 支持数据导出为PDF
- [ ] 添加推送通知功能（微信/邮件）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👨‍💻 作者

**Joins1994**

- GitHub: [@Joins1994](https://github.com/Joins1994)

## 🙏 致谢

- 新浪财经 - 提供A股实时数据
- 腾讯财经 - 提供海外指数数据
- Chart.js - 强大的图表库

---

如果你觉得这个项目有帮助，请给个 ⭐️！
