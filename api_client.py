"""
API客户端 - 处理HTTP请求和错误重试
"""
import requests
import json
import time
import random
import base64
import uuid
from typing import Dict, Any, Optional
from urllib.parse import quote
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

from config import (
    BASE_URL, LIST_API, DETAIL_API, AUTH_API, HEADERS, COOKIE,
    REQUEST_DELAY_MIN, REQUEST_DELAY_MAX, MAX_RETRIES, TIMEOUT
)

logger = logging.getLogger(__name__)


class JDLiveAPIClient:
    """京东直播API客户端"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
        # 从COOKIE中提取pin
        self.pin = self._extract_pin_from_cookie()
        
        if COOKIE:
            self.session.cookies.update({"Cookie": COOKIE})
            logger.info(f"✅ 已加载COOKIE，用户pin: {self.pin}")
        else:
            logger.warning("⚠️ 未配置 COOKIE，某些请求可能失败")
    
    def _extract_pin_from_cookie(self) -> str:
        """
        从Cookie字符串中提取pin（用户ID）
        
        Returns:
            pin值，如果未找到则返回默认值
        """
        try:
            if not COOKIE:
                return "unknown"
            
            # 查找 pin= 的位置
            pin_start = COOKIE.find("pin=")
            if pin_start == -1:
                logger.warning("⚠️ 未在Cookie中找到pin，使用默认值")
                return "unknown"
            
            # 提取pin值
            pin_start += 4  # 跳过 "pin="
            pin_end = COOKIE.find(";", pin_start)
            if pin_end == -1:
                pin_end = len(COOKIE)
            
            pin = COOKIE[pin_start:pin_end].strip()
            logger.info(f"✅ 从Cookie中提取到pin: {pin}")
            return pin
        except Exception as e:
            logger.warning(f"⚠️ 提取pin失败: {e}，使用默认值")
            return "unknown"
    
    def get_jd_eid(self) -> Optional[str]:
        """
        获取京东风险控制eid
        
        对于WebSocket鉴权，eid可以是一个生成的设备指纹
        或者从localStorage中获取。这里先使用生成的方式。
        
        Returns:
            eid字符串或None
        """
        try:
            # 方案1：使用随机生成的eid（用于测试）
            # 真实环境中应该从Selenium或localStorage获取
            eid = str(uuid.uuid4()).replace('-', '')[:40]
            logger.debug(f"✅ 生成eid: {eid}")
            return eid
        except Exception as e:
            logger.warning(f"⚠️ 获取eid失败: {e}，使用空值")
            return None
    
    def encrypt_content(self, content: Dict) -> str:
        """
        AES加密content
        
        Args:
            content: 要加密的内容字典
        
        Returns:
            base64编码的密文
        """
        key = "RYm2dMPMWD9AxYFk"
        iv = "0102030405060708"
        
        json_data = json.dumps(content, separators=(',', ':'))
        
        backend = default_backend()
        cipher = Cipher(algorithms.AES(key.encode('utf-8')), modes.CBC(iv.encode('utf-8')), backend=backend)
        encryptor = cipher.encryptor()
        
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(json_data.encode('utf-8')) + padder.finalize()
        
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        
        return base64.b64encode(encrypted).decode('utf-8')
    
    def _delay(self):
        """随机延迟3-5秒，避免被限流"""
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)
    
    def _request_with_retry(self, url: str, method: str = "GET", 
                           data: Optional[Dict] = None) -> Optional[Dict]:
        """
        带重试机制的HTTP请求
        
        Args:
            url: 请求URL
            method: HTTP方法 (GET/POST)
            data: 请求体
        
        Returns:
            响应JSON对象，失败则返回None
        """
        for attempt in range(MAX_RETRIES):
            try:
                if method == "GET":
                    resp = self.session.get(url, timeout=TIMEOUT)
                else:
                    resp = self.session.post(url, data=data, timeout=TIMEOUT)
                
                resp.raise_for_status()
                result = resp.json()
                
                # 检查京东API返回的error code
                if result.get("code") == "0" or result.get("code") == 0:
                    return result
                else:
                    error_msg = result.get("msg") or result.get("message", "Unknown error")
                    logger.error(f"API返回错误: {error_msg} | URL: {url} | 完整响应: {result}")
                    return None
                    
            except requests.exceptions.Timeout:
                logger.warning(f"请求超时 (第{attempt+1}次), 重试...")
                self._delay()
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"连接错误 (第{attempt+1}次): {str(e)}, 重试...")
                self._delay()
            except json.JSONDecodeError:
                logger.error(f"JSON解析失败 (第{attempt+1}次), 重试...")
                self._delay()
            except Exception as e:
                logger.error(f"请求失败 (第{attempt+1}次): {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    self._delay()
        
        logger.error(f"请求失败，已重试{MAX_RETRIES}次")
        return None
    
    def get_live_list(self, page: int = 1, page_size: int = 30, 
                     current_count: int = 0, filter_list: list = None,
                     last_access_data: list = None) -> Optional[Dict]:
        """
        获取直播间列表 (Feed流)
        
        Args:
            page: 页码
            page_size: 每页数量
            current_count: 已加载总数
            filter_list: 已看过的直播间ID列表
            last_access_data: 上次访问的直播间快照
        
        Returns:
            包含直播间列表的响应数据
        """
        if filter_list is None:
            filter_list = []
        if last_access_data is None:
            last_access_data = []
        
        # 构建请求体
        body = {
            "page": page,
            "pageSize": page_size,
            "currentCount": current_count,
            "lng": "9VOr64wQuppbiDV6pnul8Q",  # 加密的经度（可选）
            "lat": "3FwsAmEjfCZIGuQWw95jsA",  # 加密的纬度（可选）
            "filterList": filter_list,
            "lastAccessData": json.dumps(last_access_data) if last_access_data else "[]",
            "innerLink": None
        }
        
        # 构建URL
        url = f"{BASE_URL}?functionId={LIST_API['functionId']}&appid={LIST_API['appid']}&body={quote(json.dumps(body))}&t={int(time.time() * 1000)}"
        
        logger.info(f"📥 获取直播列表 - 页码: {page}, 页数: {page_size}")
        self._delay()
        
        return self._request_with_retry(url, method="GET")
    
    def get_live_detail(self, live_id: str) -> Optional[Dict]:
        """
        获取单个直播间详情
        
        Args:
            live_id: 直播间ID
        
        Returns:
            直播间详情数据
        """
        body = {"liveId": live_id}
        url = f"{BASE_URL}?functionId={DETAIL_API['functionId']}&appid={DETAIL_API['appid']}&body={quote(json.dumps(body))}&t={int(time.time() * 1000)}"
        
        logger.debug(f"📥 获取直播间详情 - liveId: {live_id}")
        self._delay()
        
        return self._request_with_retry(url, method="GET")
    
    def get_live_auth(self, live_id: str) -> Optional[Dict]:
        """
        获取直播间WS鉴权信息（WebSocket连接用）
        
        Args:
            live_id: 直播间ID
        
        Returns:
            包含token和WebSocket URL的鉴权数据
        """
        try:
            # 获取eid
            eid = self.get_jd_eid()
            
            # 构造content - 使用真实的pin
            content = {
                "appId": "jd.mall",
                "clientType": "m",
                "pin": self.pin,  # ✅ 使用真实的pin
                "eid": eid or "",
                "groupId": live_id,
                "timestamp": int(time.time() * 1000),
                "random": ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
            }
            
            logger.debug(f"📍 鉴权信息 - liveId: {live_id}, pin: {self.pin}, eid: {eid}")
            
            # 加密content
            encrypted_content = self.encrypt_content(content)
            
            # 构建请求参数（根据浏览器真实请求修复）
            # 关键改动：
            # 1. 使用 /liveauth 路径，不是 /api
            # 2. 改为POST方法，不是GET
            # 3. 参数在URL中，body为空
            url = "https://api.m.jd.com/liveauth"
            params = {
                "functionId": "liveauth",
                "appid": "live_pc",
                "body": json.dumps({
                    "content": encrypted_content,
                    "appId": "jd.mall"
                }),
                "t": int(time.time() * 1000)
            }
            
            # 修改特定的请求头（根据浏览器请求）
            headers = {
                "Origin": "https://zhibo.jd.com",  # 修改Origin
                "Referer": "https://zhibo.jd.com/",  # 修改Referer
                "Content-Length": "0"  # 添加Content-Length
            }
            
            logger.info(f"📥 获取WS鉴权 - liveId: {live_id}, pin: {self.pin}")
            self._delay()
            
            # 改为POST方法，注意参数在URL中
            response = self.session.post(
                url, 
                params=params, 
                headers=headers,
                timeout=TIMEOUT
            )
            response.raise_for_status()
            
            result = response.json()
            
            # 改进错误处理
            if result.get("code") == "0" or result.get("code") == 0:
                if result.get("data"):
                    logger.info(f"✅ 获取WS鉴权成功: {live_id}")
                    return result.get("data")
                else:
                    logger.warning(f"⚠️ 鉴权响应数据为空: {result}")
                    return None
            else:
                error_msg = result.get("msg") or result.get("message", "Unknown error")
                logger.error(f"❌ 鉴权失败 ({live_id}): {error_msg}")
                logger.debug(f"   完整响应: {result}")
                return None
                
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP错误 - 获取WS鉴权失败: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ 获取WS鉴权失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def close(self):
        """关闭session"""
        self.session.close()
        logger.info("✅ API客户端已关闭")
