"""
主程序 - 京东直播爬虫核心逻辑
"""
import logging
import sys
import json
from typing import List, Dict, Any

from config import DEFAULT_PAGE_SIZE, DEFAULT_PAGE, LOG_DIR, LOG_LEVEL, WS_ENABLED, WS_DURATION, WS_TEST_ROOM_LIMIT, REALTIME_CSV_FILENAME_PREFIX
from api_client import JDLiveAPIClient
from data_parser import DataParser
from csv_exporter import CSVExporter
from websocket_client import monitor_live_room

# ============== 日志配置 ==============
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"{LOG_DIR}/jd_live_crawler.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


class JDLiveCrawler:
    """京东直播爬虫主类"""
    
    def __init__(self, max_pages: int = 1, ws_enabled: bool = WS_ENABLED):
        """
        初始化爬虫
        
        Args:
            max_pages: 最多爬取页数
            ws_enabled: 是否启用WebSocket实时监控
        """
        self.api_client = JDLiveAPIClient()
        self.csv_exporter = CSVExporter()
        self.realtime_exporter = CSVExporter(filename_prefix=REALTIME_CSV_FILENAME_PREFIX) if ws_enabled else None
        self.max_pages = max_pages
        self.ws_enabled = ws_enabled
        self.stats = {
            "total_fetched": 0,  # 总共爬取的直播间数
            "total_success": 0,  # 成功解析数
            "total_failed": 0,   # 失败数
        }
    
    def crawl_single_live(self, live_id: str) -> Dict[str, Any]:
        """
        爬取单个直播间的完整数据
        
        Args:
            live_id: 直播间ID
        
        Returns:
            合并后的完整直播间数据，失败返回None
        """
        logger.info(f"🔍 正在爬取直播间: {live_id}")
        
        # 调用详情API
        detail_response = self.api_client.get_live_detail(live_id)
        
        if not detail_response:
            logger.error(f"❌ 无法获取直播间详情: {live_id}")
            self.stats["total_failed"] += 1
            return None
        
        # 解析详情数据
        try:
            detail_data = detail_response.get("data", {})
            parsed_detail = DataParser.parse_detail_item(detail_data)
            
            self.stats["total_success"] += 1
            logger.info(f"✅ 直播间爬取成功: {live_id}")
            
            # 如果启用WebSocket，监控实时数据
            if self.ws_enabled:
                logger.info(f"🔌 开始WebSocket监控: {live_id}")
                auth_response = self.api_client.get_live_auth(live_id)
                if auth_response:
                    monitor_live_room(live_id, auth_response, WS_DURATION, self.realtime_exporter)
                else:
                    logger.warning(f"⚠️ 无法获取WS鉴权: {live_id}")
            
            return parsed_detail
        
        except Exception as e:
            logger.error(f"❌ 解析详情数据失败 {live_id}: {str(e)}")
            self.stats["total_failed"] += 1
            return None
    
    def crawl_page(self, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> bool:
        """
        爬取一页直播间列表及其详情
        
        Args:
            page: 页码
            page_size: 每页数量
        
        Returns:
            成功返回True，失败返回False
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"📖 开始爬取第 {page} 页 (每页{page_size}个)")
        logger.info(f"{'='*60}")
        
        # 获取列表
        current_count = (page - 1) * page_size
        list_response = self.api_client.get_live_list(
            page=page, 
            page_size=page_size,
            current_count=current_count
        )
        
        if not list_response:
            logger.error(f"❌ 无法获取直播列表第 {page} 页")
            return False
        
        # 提取直播列表
        try:
            data = list_response.get("data", {})
            live_list = data.get("list", [])
            
            if not live_list:
                logger.warning(f"⚠️  第 {page} 页无数据，停止爬取")
                return False
            
            logger.info(f"📊 获取到 {len(live_list)} 个直播间")
            
            # 逐个爬取每个直播间的详情
            headers = DataParser.get_csv_headers()
            
            for idx, item in enumerate(live_list, 1):
                # 从列表中解析基础数据
                list_data = DataParser.parse_list_item(item)
                live_id = list_data.get("liveId")
                
                if not live_id:
                    logger.warning(f"⚠️  第 {idx} 项无liveId，跳过")
                    continue
                
                # 爬取详情
                detail_data = self.crawl_single_live(live_id)
                
                if detail_data:
                    # 合并数据并导出
                    merged_data = DataParser.merge_parsed_data(list_data, detail_data)
                    
                    if self.csv_exporter.export_row(merged_data, headers):
                        logger.debug(f"   ✓ 第{idx}个: 已保存到CSV")
                    else:
                        logger.warning(f"   ✗ 第{idx}个: CSV写入失败")
                
                self.stats["total_fetched"] += 1
                
                # 进度显示
                if idx % 5 == 0:
                    logger.info(f"   进度: {idx}/{len(live_list)}")
            
            logger.info(f"✅ 第 {page} 页爬取完成")
            return True
        
        except Exception as e:
            logger.error(f"❌ 处理列表数据失败: {str(e)}")
            return False
    
    def crawl(self):
        """
        开始爬虫主循环
        """
        logger.info("🚀 京东直播爬虫启动")
        logger.info(f"📋 配置: 最多爬取 {self.max_pages} 页")
        
        try:
            for page in range(DEFAULT_PAGE, DEFAULT_PAGE + self.max_pages):
                success = self.crawl_page(page=page)
                
                if not success:
                    logger.warning(f"⚠️  第 {page} 页爬取失败或无更多数据，停止")
                    break
                
                logger.info(f"⏸️  准备爬取下一页...")
        
        except KeyboardInterrupt:
            logger.warning("⚠️  用户中断爬虫")
        except Exception as e:
            logger.error(f"❌ 爬虫异常: {str(e)}")
        
        finally:
            self._print_statistics()
            self.api_client.close()
            self.csv_exporter.close()
            if self.realtime_exporter:
                self.realtime_exporter.close()
    
    def _print_statistics(self):
        """打印爬虫统计信息"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 爬虫统计")
        logger.info(f"{'='*60}")
        logger.info(f"✅ 成功: {self.stats['total_success']} 个")
        logger.info(f"❌ 失败: {self.stats['total_failed']} 个")
        logger.info(f"📝 总计: {self.stats['total_fetched']} 个")
        logger.info(f"{'='*60}\n")


def run_websocket_short_test():
    """
    WebSocket短时测试模式 - 只测试少量直播间的实时监控
    """
    logger.info("🔬 WebSocket短时测试模式启动")
    logger.info(f"📋 配置: 测试 {WS_TEST_ROOM_LIMIT} 个直播间, 每个监控 {WS_DURATION} 秒")
    
    # 创建API客户端
    api_client = JDLiveAPIClient()
    
    try:
        # 获取直播列表
        list_response = api_client.get_live_list(page=1, page_size=WS_TEST_ROOM_LIMIT)
        if not list_response:
            logger.error("❌ 无法获取直播列表")
            return
        
        live_list = list_response.get("data", {}).get("list", [])
        if not live_list:
            logger.warning("⚠️ 直播列表为空")
            return
        
        logger.info(f"📊 获取到 {len(live_list)} 个直播间")
        
        # 测试每个直播间的WebSocket连接
        for idx, item in enumerate(live_list[:WS_TEST_ROOM_LIMIT], 1):
            list_data = DataParser.parse_list_item(item)
            live_id = list_data.get("liveId")
            
            if not live_id:
                logger.warning(f"⚠️ 第 {idx} 项无liveId，跳过")
                continue
            
            logger.info(f"🔍 测试直播间 {idx}/{WS_TEST_ROOM_LIMIT}: {live_id}")
            
            # 创建每个直播间的单独实时数据导出器
            realtime_exporter = CSVExporter(filename_prefix=REALTIME_CSV_FILENAME_PREFIX, live_id=live_id)
            realtime_headers = DataParser.get_realtime_headers()
            
            # 获取WebSocket鉴权信息
            auth_response = api_client.get_live_auth(live_id)
            if not auth_response:
                logger.warning(f"⚠️ 无法获取WS鉴权: {live_id}，使用默认配置测试")
                auth_response = None  # 明确设置为None，让monitor_live_room使用默认配置
            
            # 监控实时数据（传入实时导出器）
            success = monitor_live_room(live_id, auth_response, WS_DURATION, realtime_exporter)
            
            if success:
                logger.info(f"✅ WebSocket测试成功: {live_id}")
            else:
                logger.error(f"❌ WebSocket测试失败: {live_id}")
            
            # 每个直播间后关闭导出器
            realtime_exporter.close()
        
    finally:
        api_client.close()


def main():
    """主入口"""
    # ============== 配置参数 ==============
    MAX_PAGES = 1  # 测试用：只爬取1页，成功后改为更多
    ENABLE_WS = False  # 是否启用WebSocket实时监控
    
    # 检查是否运行WebSocket测试模式
    if len(sys.argv) > 1 and sys.argv[1] == "ws_test":
        run_websocket_short_test()
        return
    
    # 创建爬虫并启动
    crawler = JDLiveCrawler(max_pages=MAX_PAGES, ws_enabled=ENABLE_WS)
    crawler.crawl()


if __name__ == "__main__":
    main()
