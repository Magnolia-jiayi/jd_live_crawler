"""
检查参数顺序和其他细节
"""
import json
import requests
import base64
import uuid
import time
import random
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from config import COOKIE


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
    return base64.b64encode(encrypted).decode('utf-8')


def test_parameter_order():
    """测试不同的参数顺序"""
    
    print(f"\n{'='*80}")
    print(f"🔍 测试参数顺序")
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
    
    live_id = "44756937"
    
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
    
    encrypted_content = encrypt_content(content)
    body_json = json.dumps({"content": encrypted_content, "appId": "jd.mall"})
    
    # 测试不同的参数顺序
    test_cases = [
        {
            "name": "顺序1: functionId, appid, body, t",
            "url": f"https://api.m.jd.com/liveauth?functionId=liveauth&appid=live_pc&body={requests.compat.quote(body_json)}&t={int(time.time() * 1000)}"
        },
        {
            "name": "顺序2: appid, functionId, body, t",
            "url": f"https://api.m.jd.com/liveauth?appid=live_pc&functionId=liveauth&body={requests.compat.quote(body_json)}&t={int(time.time() * 1000)}"
        },
        {
            "name": "顺序3: body, t, functionId, appid",
            "url": f"https://api.m.jd.com/liveauth?body={requests.compat.quote(body_json)}&t={int(time.time() * 1000)}&functionId=liveauth&appid=live_pc"
        }
    ]
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Origin": "https://zhibo.jd.com",
        "Referer": "https://zhibo.jd.com/",
    })
    
    if COOKIE:
        session.cookies.update({"Cookie": COOKIE})
    
    for case in test_cases:
        print(f"📌 {case['name']}")
        print(f"   URL: {case['url'][:100]}...")
        
        try:
            response = session.post(case['url'], timeout=10)
            print(f"   响应: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ 成功!")
                return True
        except Exception as e:
            print(f"   ❌ 异常: {str(e)[:50]}")
        
        print()
    
    return False


if __name__ == "__main__":
    test_parameter_order()
