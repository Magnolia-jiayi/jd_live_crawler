"""
使用POST方法的对比工具
"""
import json
import requests
import base64
from urllib.parse import quote
import uuid
import time
import random
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from config import COOKIE, HEADERS


def encrypt_content(content: dict) -> str:
    """AES加密content"""
    key = "RYm2dMPMWD9AxYFk"
    iv = "0102030405060708"
    
    json_data = json.dumps(content, separators=(',', ':'))
    
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key.encode('utf-8')), modes.CBC(iv.encode('utf-8')), backend=backend)
    encryptor = cipher.encryptor()
    
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(json_data.encode('utf-8')) + padder.finalize()
    
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')
    
    return encrypted_b64


def test_with_post():
    """使用POST方法测试"""
    
    print(f"\n{'='*80}")
    print(f"🧪 使用POST方法测试liveauth")
    print(f"{'='*80}\n")
    
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
    live_id = "44756937"
    content = {
        "appId": "jd.mall",
        "clientType": "m",
        "pin": pin,
        "eid": eid,
        "groupId": live_id,
        "timestamp": int(time.time() * 1000),
        "random": ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
    }
    
    encrypted_content = encrypt_content(content)
    
    # 方法1: 使用接近浏览器的headers和参数
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Origin": "https://zhibo.jd.com",
        "Referer": "https://zhibo.jd.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",  
        "Sec-Fetch-Site": "same-site",
        "Priority": "u=1, i"
    })
    
    if COOKIE:
        session.cookies.update({"Cookie": COOKIE})
    
    # POST请求
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
    
    print(f"📍 请求信息:")
    print(f"   URL: {url}")
    print(f"   方法: POST")
    print(f"   参数数量: {len(params)}")
    
    print(f"\n📤 发送POST请求...")
    
    try:
        response = session.post(url, params=params, timeout=10)
        
        print(f"\n✅ 响应状态码: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 200:
            print(f"\n🎉 请求成功！")
            try:
                data = response.json()
                print(f"\n📥 响应JSON:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                return True
            except:
                print(f"   响应体: {response.text[:200]}")
        else:
            print(f"\n❌ 请求失败: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    return False


if __name__ == "__main__":
    success = test_with_post()
    
    if not success:
        print(f"\n\n{'='*80}")
        print(f"💡 诊断建议:")
        print(f"{'='*80}\n")
        print("1. 再次检查浏览器的Sec-* headers")
        print("2. 验证Cookie中是否有特殊的tracking ID")
        print("3. 检查是否需要特殊的Content-Type头")
        print("4. 验证appid参数顺序")
