"""
数据解析器 - 从API响应中提取和转换字段
"""
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class DataParser:
    """数据解析和字段映射"""
    
    # 字段映射表：(原始JSON路径, CSV列名)
    # 为避免列名冲突，使用前缀区分来源
    CSV_COLUMN_MAPPING = {
        # 直播间基础信息 (来自list或detail)
        "liveId": "liveId",
        "title": "title",
        "status": "status",  # 1=直播中, 2=预告, 3=已结束
        "skuNum": "skuNum",
        "pvNum": "pvNum",
        "videoTag.liveVideoUrl": "videoTag_liveVideoUrl",
        "videoTag.liveStatus": "videoTag_liveStatus",
        "videoTag.hasPlayed": "videoTag_hasPlayed",
        "indexImage": "indexImage",
        "shareInfo.url": "shareInfo_url",
        "shareInfo.title": "shareInfo_title",
        "shareInfo.content": "shareInfo_content",
        
        # 主播信息
        "authorInfo.authorId": "authorId",
        "authorInfo.pin": "authorInfo_pin",
        "authorInfo.name": "authorInfo_name",
        "authorInfo.avatar": "authorInfo_avatar",
        "authorInfo.fansNum": "authorInfo_fansNum",
        "authorInfo.isOfficial": "authorInfo_isOfficial",
        "authorInfo.shopId": "shopId",
        "authorInfo.location": "authorInfo_location",
        "authorInfo.fansLevel": "authorInfo_fansLevel",
        
        # 配置信息
        "configInfo.style": "configInfo_style",
        "configInfo.isBindPhone": "configInfo_isBindPhone",
        "configInfo.userMemberLevel": "configInfo_userMemberLevel",
    }
    
    @staticmethod
    def _get_nested_value(obj: Dict, path: str, default: Any = None) -> Any:
        """
        从嵌套字典中获取值
        
        Args:
            obj: 字典对象
            path: 路径，如 "a.b.c"
            default: 默认值
        
        Returns:
            值或默认值
        """
        keys = path.split(".")
        current = obj
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return default
            
            if current is None:
                return default
        
        return current if current is not None else default
    
    @staticmethod
    def _serialize_value(value: Any) -> str:
        """
        序列化值为字符串（处理列表、字典等复杂类型）
        
        Args:
            value: 任意值
        
        Returns:
            字符串形式的值
        """
        if value is None:
            return ""
        elif isinstance(value, bool):
            return "1" if value else "0"
        elif isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        else:
            return str(value)
    
    @classmethod
    def parse_list_item(cls, item: Dict) -> Dict[str, Any]:
        """
        解析直播列表中的单个直播间数据
        
        Args:
            item: 直播列表中的单个项 (data.list[])
        
        Returns:
            解析后的直播间数据字典
        """
        parsed = {}
        author_card = item.get("authorCard", {})
        
        # 提取authorCard中的字段
        parsed["liveId"] = author_card.get("id") or author_card.get("liveId")
        parsed["title"] = author_card.get("title", "")
        parsed["status"] = "unknown"  # 列表中无status
        parsed["skuNum"] = author_card.get("skuNum", "")
        parsed["pvNum"] = author_card.get("pv", "")
        parsed["videoTag_liveVideoUrl"] = cls._get_nested_value(author_card, "videoTag.liveVideoUrl", "")
        parsed["videoTag_liveStatus"] = cls._get_nested_value(author_card, "videoTag.liveStatus", "")
        parsed["videoTag_hasPlayed"] = cls._get_nested_value(author_card, "videoTag.hasPlayed", "")
        parsed["indexImage"] = author_card.get("indexImage", "")
        
        # 主播信息
        parsed["authorId"] = author_card.get("authorId", "")
        parsed["authorInfo_name"] = author_card.get("userName", "")
        parsed["authorInfo_avatar"] = author_card.get("userPic", "")
        parsed["authorInfo_fansNum"] = ""  # 列表中无粉丝数
        parsed["authorInfo_isOfficial"] = ""
        parsed["shopId"] = ""  # 列表中无shopId
        parsed["authorInfo_location"] = ""
        parsed["authorInfo_fansLevel"] = ""
        
        # 埋点信息（保存原始JSON字符串）
        parsed["buryInfo_raw"] = author_card.get("buryInfo", "")
        
        return parsed
    
    @classmethod
    def parse_detail_item(cls, detail: Dict) -> Dict[str, Any]:
        """
        解析单直播间详情数据
        
        Args:
            detail: 详情页API响应中的data字段
        
        Returns:
            解析后的直播间完整数据字典
        """
        parsed = {}
        
        # 直播间基础信息
        parsed["liveId"] = detail.get("liveId", "")
        parsed["title"] = detail.get("title", "")
        parsed["status"] = detail.get("status", "")
        parsed["skuNum"] = detail.get("skuNum", "")
        parsed["pvNum"] = detail.get("pvNum", "")
        parsed["videoTag_liveVideoUrl"] = cls._get_nested_value(detail, "videoTag.liveVideoUrl", "")
        parsed["videoTag_liveStatus"] = cls._get_nested_value(detail, "videoTag.liveStatus", "")
        parsed["videoTag_hasPlayed"] = cls._get_nested_value(detail, "videoTag.hasPlayed", "")
        parsed["indexImage"] = detail.get("indexImage", "")
        
        # shareInfo
        parsed["shareInfo_url"] = cls._get_nested_value(detail, "shareInfo.url", "")
        parsed["shareInfo_title"] = cls._get_nested_value(detail, "shareInfo.title", "")
        parsed["shareInfo_content"] = cls._get_nested_value(detail, "shareInfo.content", "")
        
        # 主播信息
        author_info = detail.get("authorInfo", {})
        parsed["authorId"] = author_info.get("authorId", "")
        parsed["authorInfo_pin"] = author_info.get("pin", "")
        parsed["authorInfo_name"] = author_info.get("name", "")
        parsed["authorInfo_avatar"] = author_info.get("avatar", "")
        parsed["authorInfo_fansNum"] = author_info.get("fansNum", "")
        parsed["authorInfo_isOfficial"] = author_info.get("isOfficial", "")
        parsed["shopId"] = author_info.get("shopId", "")
        parsed["authorInfo_location"] = author_info.get("location", "")
        parsed["authorInfo_fansLevel"] = author_info.get("fansLevel", "")
        
        # 配置信息
        config_info = detail.get("configInfo", {})
        parsed["configInfo_style"] = config_info.get("style", "")
        parsed["configInfo_isBindPhone"] = config_info.get("isBindPhone", "")
        parsed["configInfo_userMemberLevel"] = config_info.get("userMemberLevel", "")
        
        # 历史聊天 (转为JSON字符串)
        chat_list = detail.get("historyChatList", [])
        parsed["historyChatList"] = cls._serialize_value(chat_list)
        parsed["historyChatList_count"] = len(chat_list)
        
        # 其他字段
        parsed["welcome"] = detail.get("welcome", "")
        parsed["loginStatus"] = detail.get("loginStatus", "")
        parsed["configInfo_nickName"] = config_info.get("nickName", "")
        
        # 数据采集时间
        parsed["crawl_time"] = datetime.now().isoformat()
        
        return parsed
    
    @classmethod
    def merge_parsed_data(cls, list_data: Dict, detail_data: Dict) -> Dict:
        """
        合并列表数据和详情数据（优先使用详情数据）
        
        Args:
            list_data: 从列表API解析的数据
            detail_data: 从详情API解析的数据
        
        Returns:
            合并后的完整数据
        """
        merged = dict(list_data)  # 先复制列表数据
        
        # 用详情数据覆盖（详情数据更完整）
        for key, value in detail_data.items():
            if value != "" and value is not None:
                merged[key] = value
        
        return merged
    
    @classmethod
    def get_csv_headers(cls) -> List[str]:
        """
        获取CSV列头列表
        
        Returns:
            有序的列名列表
        """
        base_headers = [
            "liveId", "title", "status", "skuNum", "pvNum",
            "videoTag_liveVideoUrl", "videoTag_liveStatus", "videoTag_hasPlayed",
            "indexImage", "shareInfo_url", "shareInfo_title", "shareInfo_content",
            "authorId", "authorInfo_pin", "authorInfo_name", "authorInfo_avatar",
            "authorInfo_fansNum", "authorInfo_isOfficial", "shopId",
            "authorInfo_location", "authorInfo_fansLevel",
            "configInfo_style", "configInfo_isBindPhone", "configInfo_userMemberLevel",
            "configInfo_nickName", "welcome", "loginStatus",
            "historyChatList", "historyChatList_count",
            "buryInfo_raw", "crawl_time"
        ]
        return base_headers
    
    @classmethod
    def parse_ws_event(cls, event_type: str, event_data: Dict[str, Any], live_id: str) -> Dict[str, Any]:
        """
        解析WebSocket事件为CSV行数据
        
        Args:
            event_type: 事件类型（如 "chat", "stats", "gift"）
            event_data: 事件数据字典
            live_id: 直播间ID
        
        Returns:
            平铺的CSV行数据字典
        """
        from datetime import datetime
        
        parsed = {
            "liveId": live_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "raw_data": cls._serialize_value(event_data)
        }
        
        # 根据事件类型提取特定字段
        if event_type == "chat":
            parsed["message"] = event_data.get("content", "")
            parsed["user"] = event_data.get("user", "")
        elif event_type == "stats":
            parsed["viewer_count"] = event_data.get("viewers", 0)
            parsed["thumbs_up"] = event_data.get("likes", 0)
        elif event_type == "gift":
            parsed["gift_info"] = event_data.get("gift", "")
            parsed["user"] = event_data.get("user", "")
        elif event_type == "join":
            parsed["user"] = event_data.get("nickName", "")
            parsed["message"] = event_data.get("content", "")
        elif event_type == "jdlive_refresh_cart":
            parsed["cart_number"] = event_data.get("cartNumber", 0)
            parsed["cart_items"] = cls._serialize_value(event_data.get("cartItems", []))
        elif event_type == "anchor_new_popup_product":
            parsed["product_info"] = cls._serialize_value(event_data.get("product", {}))
            parsed["popup_type"] = event_data.get("type", "")
        elif event_type == "anchor_start_live" or event_type == "anchor_end_live":
            parsed["live_status"] = event_data.get("status", "")
            parsed["start_time"] = event_data.get("startTime", "")
        elif event_type == "user_follow":
            parsed["follower"] = event_data.get("user", "")
            parsed["followed_user"] = event_data.get("followedUser", "")
        else:
            # 其他未知事件类型，记录所有字段
            for key, value in event_data.items():
                if key not in parsed:
                    parsed[f"extra_{key}"] = cls._serialize_value(value)
        
        return parsed
    
    @classmethod
    def get_realtime_headers(cls) -> List[str]:
        """
        获取实时事件CSV列头列表
        
        Returns:
            有序的列名列表
        """
        headers = [
            "liveId", "timestamp", "event_type", "raw_data",
            "message", "user", "viewer_count", "thumbs_up", "gift_info",
            "cart_number", "cart_items", "product_info", "popup_type",
            "live_status", "start_time", "follower", "followed_user"
        ]
        return headers
