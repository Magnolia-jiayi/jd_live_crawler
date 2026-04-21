"""
对比工具 - 用于检查代码发送的请求与浏览器真实请求的差异
"""
import json
import requests
from urllib.parse import quote
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import uuid
import time
import random
from config import COOKIE, HEADERS


class RequestComparator:
    """请求对比工具"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        if COOKIE:
            self.session.cookies.update({"Cookie": COOKIE})
    
    def encrypt_content(self, content: dict) -> str:
        """AES加密content"""
        key = "RYm2dMPMWD9AxYFk"
        iv = "0102030405060708"
        
        json_data = json.dumps(content, separators=(',', ':'))
        print(f"\n📄 加密前的content JSON:\n{json_data}\n")
        
        backend = default_backend()
        cipher = Cipher(algorithms.AES(key.encode('utf-8')), modes.CBC(iv.encode('utf-8')), backend=backend)
        encryptor = cipher.encryptor()
        
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(json_data.encode('utf-8')) + padder.finalize()
        
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')
        
        print(f"🔐 加密后的content (Base64):\n{encrypted_b64}\n")
        return encrypted_b64
    
    def build_auth_request(self, live_id: str) -> dict:
        """构建鉴权请求"""
        
        # 提取pin
        pin = "unknown"
        if COOKIE:
            pin_start = COOKIE.find("pin=")
            if pin_start != -1:
                pin_start += 4
                pin_end = COOKIE.find(";", pin_start)
                if pin_end == -1:
                    pin_end = len(COOKIE)
                pin = COOKIE[pin_start:pin_end].strip()
        
        # 生成eid
        eid = str(uuid.uuid4()).replace('-', '')[:40]
        
        # 构造content
        content = {
            "appId": "jd.mall",
            "clientType": "m",
            "pin": pin,
            "eid": eid,
            "groupId": live_id,
            "timestamp": int(time.time() * 1000),
            "random": ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
        }
        
        print(f"\n{'='*80}")
        print(f"📝 构建的鉴权请求信息")
        print(f"{'='*80}")
        print(f"\n🏪 直播间ID: {live_id}")
        print(f"👤 用户Pin: {pin}")
        print(f"🔑 设备EID: {eid}")
        print(f"⏰ 时间戳: {content['timestamp']}")
        print(f"🎲 随机值: {content['random']}")
        
        # 加密
        encrypted_content = self.encrypt_content(content)
        
        # 构建请求体
        request_body = {
            "content": encrypted_content,
            "appId": "jd.mall"
        }
        
        # 构建完整URL
        url = "https://api.m.jd.com/api"
        params = {
            "functionId": "liveauth",
            "body": json.dumps(request_body),
            "t": int(time.time() * 1000),
            "appid": "live_pc"
        }
        
        return {
            "url": url,
            "params": params,
            "body": request_body,
            "headers": dict(self.session.headers)
        }
    
    def send_and_analyze(self, live_id: str):
        """发送请求并分析结果"""
        
        request_info = self.build_auth_request(live_id)
        
        print(f"\n{'='*80}")
        print(f"🌐 完整请求信息")
        print(f"{'='*80}")
        print(f"\n📍 Base URL: {request_info['url']}")
        print(f"\n📋 Query 参数:")
        for key, value in request_info['params'].items():
            if key == 'body':
                print(f"   {key}: [已加密的JSON]")
            else:
                print(f"   {key}: {value}")
        
        print(f"\n📤 Request Headers:")
        for key, value in request_info['headers'].items():
            print(f"   {key}: {value}")
        
        print(f"\n{'='*80}")
        print(f"🚀 发送请求...")
        print(f"{'='*80}\n")
        
        try:
            # 发送请求
            response = self.session.get(
                request_info['url'],
                params=request_info['params'],
                timeout=30
            )
            
            print(f"📊 响应信息:")
            print(f"   状态码: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('Content-Type')}")
            
            print(f"\n📥 响应体:")
            try:
                resp_json = response.json()
                print(json.dumps(resp_json, indent=2, ensure_ascii=False))
            except:
                print(response.text[:500])
            
            # 分析错误
            if response.status_code == 403:
                print(f"\n❌ 获得403 Forbidden 错误")
                print(f"\n🔍 可能的原因:")
                print(f"   1. Cookie过期或无效")
                print(f"   2. 加密参数不正确")
                print(f"   3. 缺少必要的请求头")
                print(f"   4. 请求被京东风控系统识别为异常")
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
    
    def compare_with_browser_request(self):
        """指导用户对比浏览器请求"""
        print(f"\n{'='*80}")
        print(f"🔍 与浏览器真实请求对比检查清单")
        print(f"{'='*80}\n")
        
        print("请打开浏览器开发者工具，按以下步骤对比：\n")
        
        print("1️⃣  打开 https://lives.jd.com")
        print("2️⃣  按F12打开开发者工具")
        print("3️⃣  进入Network标签页")
        print("4️⃣  在Filter输入框输入 'liveauth'")
        print("5️⃣  刷新页面或进入直播间（触发鉴权请求）")
        print("6️⃣  找到functionId=liveauth的请求\n")
        
        print("记录以下信息并与上面的输出对比：\n")
        
        print("【Request信息对比】")
        print("☐ URL 路径是否相同？")
        print("   浏览器: https://api.m.jd.com/api?functionId=liveauth&...")
        print("   代码:   https://api.m.jd.com/api?functionId=liveauth&...\n")
        
        print("【Query参数对比】")
        print("☐ functionId: 是否都是 'liveauth'？")
        print("☐ appid: 是否都是 'live_pc'？")
        print("☐ body: 加密的content是否格式相同？")
        print("☐ t: 时间戳值是否类似（仅作参考）？")
        print("")
        
        print("【Headers对比】")
        print("☐ Cookie: 是否包含 pin=jd_xxx？")
        print("☐ User-Agent: 是否相同？")
        print("☐ Content-Type: 浏览器发送了什么？")
        print("☐ Referer: 是否需要这个头？")
        print("")
        
        print("【Response对比】")
        print("☐ 浏览器得到什么响应？ (200? 403? 其他?)")
        print("☐ 响应中的data字段包含什么？")
        print("☐ code字段的值是什么？\n")
        
        print("如果发现差异，请在 debugged_requests.json 中记录浏览器的真实请求")


def main():
    """主函数"""
    comparator = RequestComparator()
    
    # 测试直播间ID
    live_id = "44898172"
    
    print(f"\n🎬 开始对比鉴权请求...")
    comparator.send_and_analyze(live_id)
    
    print(f"\n")
    comparator.compare_with_browser_request()


if __name__ == "__main__":
    main()
