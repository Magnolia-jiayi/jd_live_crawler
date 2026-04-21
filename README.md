# 京东直播爬虫

用Python编写的京东直播数据爬虫，可自动爬取直播间基础信息、主播信息、实时统计等数据。

## 📋 功能

- ✅ 爬取直播列表（支持Feed流翻页）
- ✅ 获取单个直播间完整详情
- ✅ 提取主播信息、配置、历史聊天等
- ✅ 自动重试机制（网络错误、超时）
- ✅ 数据导出为CSV（UTF-8编码、Excel兼容）
- ✅ 详细日志记录

## 🗂️ 项目结构

```
jd_live_crawler/
├── main.py                # 主程序入口
├── api_client.py          # API客户端
├── data_parser.py         # 数据解析器
├── csv_exporter.py        # CSV导出器
├── config.py              # 配置文件
├── requirements.txt       # 依赖列表
├── .env.example           # 环境变量示例
├── .gitignore             # Git忽略文件
├── README.md              # 本文件
├── output/                # 输出目录（自动创建）
└── logs/                  # 日志目录（自动创建）
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置认证信息

**获取Cookie步骤：**

1. 打开浏览器，访问 https://lives.jd.com
2. 出现登录页，用你的京东账号登录
3. 登录后，在页面任何地方右键 → 检查 → 按F12打开开发者工具
4. 点击 Network 标签
5. 刷新页面，找到任何 api.m.jd.com 的请求
6. 点击该请求，在 Request Headers 中找到 Cookie
7. 复制整个 Cookie 值（从 `pt_` 开头到最后）

**环境变量配置：**

1. 复制 `.env.example` 为 `.env`
   ```bash
   cp .env.example .env
   ```

2. 用文本编辑器打开 `.env`，粘贴你的Cookie
   ```
   COOKIE="将你的Cookie粘贴在这里"
   ```

### 3. 运行爬虫

```bash
python main.py
```

首次运行会爬取第1页（30个直播间），验证配置是否正确。

## 📊 数据输出

爬虫完成后，会在 `output/` 目录生成CSV文件（格式：`jd_live_data_时间戳.csv`）

### 主要字段说明

| 字段名 | 说明 | 来源 |
|---|---|---|
| liveId | 直播间ID | 列表API |
| title | 直播间标题 | 列表/详情API |
| status | 直播状态 (1=直播中, 2=预告, 3=已结束) | 详情API |
| authorId | 主播ID | 列表/详情API |
| authorInfo_name | 主播昵称 | 列表/详情API |
| shopId | 店铺ID | 详情API |
| skuNum | 商品数量 | 列表/详情API |
| pvNum | 页面访问量 | 列表/详情API |
| authorInfo_fansNum | 粉丝数 | 详情API |
| historyChatList | 历史聊天记录 (JSON格式) | 详情API |
| crawl_time | 爬取时间 | 本地系统 |

## ⚙️ 配置说明

编辑 `config.py` 中的参数：

```python
# 请求配置
REQUEST_DELAY_MIN = 3      # 最小延迟（秒）
REQUEST_DELAY_MAX = 5      # 最大延迟（秒）
MAX_RETRIES = 3            # 最大重试次数
TIMEOUT = 30               # 请求超时（秒）

# 分页配置  
DEFAULT_PAGE_SIZE = 30     # 每页数量
DEFAULT_PAGE = 1           # 起始页码

# 输出配置
CSV_OUTPUT_DIR = "./output"  # CSV输出目录
CSV_ENCODING = "utf-8-sig"   # UTF-8 with BOM
```

编辑 `main.py` 中的爬取页数：

```python
MAX_PAGES = 1  # 修改为你想要的页数（1页=30个直播间）
```

## 📝 日志记录

爬虫会输出详细日志到：
- **控制台**：实时显示爬虫进度
- **文件**：`logs/jd_live_crawler.log`

日志级别：INFO（显示关键步骤和错误）

## 🔧 故障排查

### 1. 请求失败 "API返回错误"

**原因**：Cookie已过期或无效

**解决**：重新获取Cookie并更新 `.env` 文件

### 2. 连接超时

**原因**：网络问题或京东服务器无响应

**解决**：增加 `REQUEST_DELAY_MAX` 或 `TIMEOUT` 值

### 3. CSV文件为空

**原因**：爬取失败或无数据

**解决**：查看 `logs/jd_live_crawler.log` 查找错误信息

## ⚠️ 免责声明

- 本爬虫仅供学习和研究使用
- 请遵守京东服务条款，不要过度爬取
- 建议爬取间隔设置为3-5秒，避免被限流
- 不要用爬虫进行商业用途

## 📌 后续功能规划

- [ ] WebSocket实时监听（直播统计、聊天消息）
- [ ] 品牌白名单过滤
- [ ] 数据库存储支持
- [ ] 异步并发爬取
- [ ] Web界面管理

## 📧 反馈与改进

有任何问题或建议，欢迎提出！
