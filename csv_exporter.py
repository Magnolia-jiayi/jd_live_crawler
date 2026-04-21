"""
CSV导出器 - 将爬取的数据写入CSV文件
"""
import csv
import os
import logging
from datetime import datetime
from typing import List, Dict, Any

from config import CSV_OUTPUT_DIR, CSV_ENCODING, CSV_SEPARATOR, REALTIME_CSV_FILENAME_PREFIX
from data_parser import DataParser

logger = logging.getLogger(__name__)


class CSVExporter:
    """CSV文件导出器"""
    
    def __init__(self, filename_prefix: str = "jd_live_data_", live_id: str = None):
        """
        初始化导出器，生成输出文件名
        
        Args:
            filename_prefix: 文件名前缀，默认 "jd_live_data_"
            live_id: 直播间ID，用于创建单独的文件
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if live_id:
            self.filename = os.path.join(CSV_OUTPUT_DIR, f"realtime_{live_id}_{timestamp}.csv")
        else:
            self.filename = os.path.join(CSV_OUTPUT_DIR, f"{filename_prefix}{timestamp}.csv")
        self.is_header_written = False
        self.count = 0
    
    def export_row(self, data: Dict[str, Any], headers: List[str] = None) -> bool:
        """
        导出单行数据到CSV
        
        Args:
            data: 数据字典
            headers: CSV列头（首次写入时自动写入）
        
        Returns:
            成功返回True，失败返回False
        """
        if headers is None:
            headers = DataParser.get_csv_headers()
        
        try:
            # 确定文件是否已存在
            file_exists = os.path.exists(self.filename)
            
            with open(self.filename, "a", newline="", encoding=CSV_ENCODING) as f:
                writer = csv.DictWriter(
                    f, 
                    fieldnames=headers, 
                    restval="",  # 缺失字段用空字符串填充
                    extrasaction="ignore",  # 忽略多余的字段
                    delimiter=CSV_SEPARATOR
                )
                
                # 如果文件不存在或为空，写入头部
                if not file_exists and not self.is_header_written:
                    writer.writeheader()
                    self.is_header_written = True
                    logger.info(f"📝 创建CSV文件: {self.filename}")
                
                # 写入数据行
                writer.writerow(data)
                self.count += 1
                
                return True
        
        except IOError as e:
            logger.error(f"✗ CSV写入失败: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"✗ 未知错误: {str(e)}")
            return False
    
    def export_batch(self, data_list: List[Dict[str, Any]], 
                    headers: List[str] = None) -> int:
        """
        批量导出数据
        
        Args:
            data_list: 数据列表
            headers: CSV列头
        
        Returns:
            成功导出的行数
        """
        if not headers:
            headers = DataParser.get_csv_headers()
        
        success_count = 0
        for data in data_list:
            if self.export_row(data, headers):
                success_count += 1
        
        return success_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取导出统计信息
        
        Returns:
            统计字典
        """
        return {
            "csv_file": self.filename,
            "total_rows": self.count,
            "file_exists": os.path.exists(self.filename),
            "file_size_kb": os.path.getsize(self.filename) / 1024 if os.path.exists(self.filename) else 0
        }
    
    def close(self):
        """关闭导出器并输出统计信息"""
        stats = self.get_statistics()
        logger.info(f"✅ CSV导出完成!")
        logger.info(f"   📄 文件: {stats['csv_file']}")
        logger.info(f"   📊 行数: {stats['total_rows']}")
        logger.info(f"   💾 大小: {stats['file_size_kb']:.2f} KB")
