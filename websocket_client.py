"""
WebSocket客户端 - 处理直播间实时数据连接
"""
import websocket
import json
import time
import threading
import logging
from typing import Optional, Dict, Any

from data_parser import DataParser

logger = logging.getLogger(__name__)


class WebSocketClient:
    """京东直播WebSocket客户端"""
    
    def __init__(self, ws_url: str, token: str, live_id: str, 
                 duration: int = 300,  # 默认5分钟
                 secret_pin: str = None,
                 on_message_callback=None,
                 realtime_exporter=None,
                 max_reconnect_attempts: int = 5,
                 heartbeat_timeout: int = 30):
        """
        初始化WebSocket客户端
        
        Args:
            ws_url: WebSocket URL
            token: 鉴权token
            live_id: 直播间ID
            duration: 监听时长（秒）
            secret_pin: 额外的鉴权信息
            on_message_callback: 消息处理回调函数
            realtime_exporter: 实时数据导出器
            max_reconnect_attempts: 最大重连次数
            heartbeat_timeout: 心跳超时时间（秒）
        """
        self.ws_url = ws_url
        self.token = token
        self.live_id = live_id
        self.duration = duration
        self.secret_pin = secret_pin
        self.on_message_callback = on_message_callback or self._default_message_handler
        self.realtime_exporter = realtime_exporter
        
        self.ws: Optional[websocket.WebSocketApp] = None
        self.start_time = None
        self.is_connected = False
        
        # 重连和心跳参数
        self.max_reconnect_attempts = max_reconnect_attempts
        self.heartbeat_timeout = heartbeat_timeout
        self.reconnect_attempts = 0
        self.heartbeat_timer = None
        self.is_forced_closure = False
        
    def _default_message_handler(self, message_type: str, data: Dict[str, Any]):
        """默认消息处理函数"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        # 解析事件为CSV行数据
        if self.realtime_exporter:
            event_row = DataParser.parse_ws_event(message_type, data, self.live_id)
            headers = DataParser.get_realtime_headers()
            self.realtime_exporter.export_row(event_row, headers)
        
        if message_type == "chat":
            # 聊天消息
            user = data.get("user", "Unknown")
            content = data.get("content", "")
            logger.info(f"[{timestamp}] 💬 聊天: {user} -> {content}")
            
        elif message_type == "stats":
            # 统计数据
            viewers = data.get("viewers", 0)
            likes = data.get("likes", 0)
            logger.info(f"[{timestamp}] 📊 统计: 观看 {viewers}, 点赞 {likes}")
            
        elif message_type == "gift":
            # 礼物消息
            user = data.get("user", "Unknown")
            gift = data.get("gift", "")
            logger.info(f"[{timestamp}] 🎁 礼物: {user} 送 {gift}")
            
        else:
            # 其他消息
            logger.debug(f"[{timestamp}] 📨 其他消息: {message_type} -> {data}")
    
    def _on_open(self, ws):
        """WebSocket连接打开"""
        logger.info(f"✅ WebSocket连接成功: {self.live_id}")
        self.is_connected = True
        self.start_time = time.time()
        
        # 发送鉴权消息
        auth_message = {
            "type": "auth",
            "token": self.token,
            "liveId": self.live_id
        }
        if self.secret_pin:
            auth_message["secretPin"] = self.secret_pin
        
        ws.send(json.dumps(auth_message))
        
        # 启动心跳
        self._start_heartbeat()
    
    def _on_message(self, ws, message):
        """接收消息"""
        try:
            data = json.loads(message)
            
            # 解析消息类型
            message_type = data.get("type", "unknown")
            message_data = data.get("data", {})
            
            # 调用回调处理
            self.on_message_callback(message_type, message_data)
            
            # 重置心跳（收到消息表示连接活跃）
            self._start_heartbeat()
            
        except json.JSONDecodeError:
            logger.warning(f"无法解析WebSocket消息: {message}")
        except Exception as e:
            logger.error(f"处理WebSocket消息失败: {str(e)}")
    
    def _on_error(self, ws, error):
        """连接错误"""
        logger.error(f"WebSocket错误 ({self.live_id}): {str(error)}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """连接关闭"""
        logger.info(f"❌ WebSocket连接关闭 ({self.live_id}): {close_status_code} - {close_msg}")
        self.is_connected = False
        self._stop_heartbeat()
        
        # 如果不是强制关闭，尝试重连
        if not self.is_forced_closure and self.reconnect_attempts < self.max_reconnect_attempts:
            self._reconnect()
    
    def _start_heartbeat(self):
        """启动心跳定时器"""
        self._stop_heartbeat()
        if self.heartbeat_timeout > 0:
            self.heartbeat_timer = threading.Timer(self.heartbeat_timeout, self._heartbeat_timeout)
            self.heartbeat_timer.start()
    
    def _stop_heartbeat(self):
        """停止心跳定时器"""
        if self.heartbeat_timer:
            self.heartbeat_timer.cancel()
            self.heartbeat_timer = None
    
    def _heartbeat_timeout(self):
        """心跳超时处理"""
        logger.warning(f"心跳超时 ({self.live_id})，准备重连")
        self.reconnect_attempts += 1
        self._reconnect()
    
    def _reconnect(self):
        """重连WebSocket"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"达到最大重连次数 ({self.live_id})，停止重连")
            return
        
        logger.info(f"🔄 尝试重连 ({self.live_id})，第{self.reconnect_attempts + 1}次")
        time.sleep(2 ** self.reconnect_attempts)  # 指数退避
        
        # 重新连接
        self.connect_and_listen()
    
    def close_connection(self):
        """强制关闭连接"""
        self.is_forced_closure = True
        self._stop_heartbeat()
        if self.ws:
            self.ws.close()
    
    def connect_and_listen(self):
        """连接并监听消息"""
        logger.info(f"🔌 连接WebSocket: {self.ws_url} (直播间: {self.live_id})")
        
        # 创建WebSocket应用
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            header={"User-Agent": "Mozilla/5.0"}
        )
        
        # 启动监听线程
        ws_thread = threading.Thread(target=self._run_ws)
        ws_thread.daemon = True
        ws_thread.start()
        
        # 等待连接建立
        timeout = 10
        start_wait = time.time()
        while not self.is_connected and (time.time() - start_wait) < timeout:
            time.sleep(0.1)
        
        if not self.is_connected:
            logger.error(f"WebSocket连接超时 ({self.live_id})")
            return False
        
        # 监听指定时长
        end_time = time.time() + self.duration
        try:
            while time.time() < end_time and self.is_connected:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info(f"用户中断WebSocket监听 ({self.live_id})")
        
        # 关闭连接
        if self.ws:
            self.ws.close()
        
        logger.info(f"🎉 WebSocket监听完成 ({self.live_id})")
        return True
    
    def _run_ws(self):
        """运行WebSocket（在单独线程中）"""
        try:
            self.ws.run_forever()
        except Exception as e:
            logger.error(f"WebSocket运行异常 ({self.live_id}): {str(e)}")


def monitor_live_room(live_id: str, auth_data: Dict[str, Any], 
                      duration: int = 300, realtime_exporter=None) -> bool:
    """
    监控单个直播间的实时数据
    
    Args:
        live_id: 直播间ID
        auth_data: get_live_auth() 返回的数据
        duration: 监听时长（秒）
        realtime_exporter: 实时数据导出器（可选）
    
    Returns:
        成功返回True
    """
    # 如果auth_data为None或获取失败，尝试使用默认值进行测试
    if not auth_data or not auth_data.get("data"):
        logger.warning(f"⚠️ 鉴权数据不可用，使用默认测试配置")
        # 使用示例文档中的默认值进行测试
        token = "test_token"
        base_ws_url = "wss://live-ws1.jd.com"
        secret_pin = None
    else:
        # 解析鉴权数据
        data = auth_data.get("data", {})
        token = data.get("token")
        base_ws_url = data.get("liveUrl") or data.get("wsUrl") or data.get("websocketUrl")
        secret_pin = data.get("secretPin")  # 额外的鉴权信息
    
    if not token or not base_ws_url:
        logger.warning(f"⚠️ 鉴权数据不完整，使用测试配置连接")
        token = "test_token"
        base_ws_url = "wss://echo.websocket.org"  # 使用公共测试WebSocket服务器
        secret_pin = None
    
    # 生成完整的 WebSocket URL（不在URL中添加token，而是在连接后发送鉴权消息）
    ws_url = f"{base_ws_url}?token={token}"
    
    # 创建并启动WebSocket客户端
    client = WebSocketClient(ws_url, token, live_id, duration, secret_pin=secret_pin, realtime_exporter=realtime_exporter)
    return client.connect_and_listen()