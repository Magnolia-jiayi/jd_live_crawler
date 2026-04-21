"""
配置文件 - API端点、请求头、常量设置
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# ============== API 端点 ===========
BASE_URL = "https://api.m.jd.com/api"

LIST_API = {
    "functionId": "predictLiveListToM",
    "appid": "live_pc"
}

DETAIL_API = {
    "functionId": "liveBasicDetailToM",
    "appid": "live_pc"
}

# WebSocket鉴权API - 尝试不同的配置
AUTH_API = {
    "functionId": "liveauth",
    "appid": "live_pc",
    "base_url": "https://api.m.jd.com"  # 使用正确的base_url
}

# ============== 请求头 ==============
HEADERS = {    "User-Agent": os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
    "Referer": "https://lives.jd.com",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# Cookie（从 .env 读取）
COOKIE = os.getenv("COOKIE", "")

# ============== 爬虫参数 ==============
REQUEST_DELAY_MIN = 3  # 最小延迟（秒）
REQUEST_DELAY_MAX = 5  # 最大延迟（秒）
MAX_RETRIES = 3  # 最大重试次数
TIMEOUT = 30  # 请求超时（秒）

# ============== 分页参数 ==============
DEFAULT_PAGE_SIZE = 2  # 每页直播间数（测试用：只抓取2个）
DEFAULT_PAGE = 1  # 起始页码

# ============== WebSocket 设置 ==============
WS_ENABLED = True  # 是否启用WebSocket实时监控（测试用：启用）
WS_DURATION = 10   # 每个直播间监控时长（秒）（测试用：10秒）
WS_CONNECTION_TIMEOUT = 10  # WebSocket连接超时（秒）
WS_TEST_ROOM_LIMIT = 2  # WebSocket测试房间数量限制

# ============== CSV 设置 ==============
CSV_OUTPUT_DIR = "./output"  # CSV输出目录
CSV_ENCODING = "utf-8-sig"  # UTF-8 with BOM（Excel可直接打开）
CSV_SEPARATOR = ","
REALTIME_CSV_FILENAME_PREFIX = "jd_live_realtime_"  # 实时数据CSV文件名前缀

# ============== 日志设置 ==============
LOG_DIR = "./logs"
LOG_LEVEL = "INFO"

# ============== 品牌筛选 ==============
BRAND_FILTER_ENABLED = False  # 是否启用品牌筛选
BRAND_WHITELIST_FILE = "./brand_whitelist.xlsx"  # 品牌白名单文件路径

# 确保输出目录存在
if not os.path.exists(CSV_OUTPUT_DIR):
    os.makedirs(CSV_OUTPUT_DIR)

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
