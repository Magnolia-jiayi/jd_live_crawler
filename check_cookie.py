"""
检查Cookie有效性
"""
import requests
from config import COOKIE


def check_cookie_validity():
    """检查Cookie是否有效"""
    
    print(f"\n{'='*80}")
    print(f"🔍 检查Cookie有效性")
    print(f"{'='*80}\n")
    
    # 检查1: Cookie长度
    if not COOKIE:
        print("❌ COOKIE 为空！")
        print("   请在 .env 文件中配置 COOKIE 值")
        return False
    
    cookie_len = len(COOKIE)
    print(f"✅ Cookie 长度: {cookie_len} 字符")
    if cookie_len < 100:
        print("⚠️  警告: Cookie看起来太短了，可能不完整")
    
    # 检查2: pin 是否存在
    if "pin=" in COOKIE:
        pin_start = COOKIE.find("pin=") + 4
        pin_end = COOKIE.find(";", pin_start)
        if pin_end == -1:
            pin_end = len(COOKIE)
        pin = COOKIE[pin_start:pin_end].strip()
        print(f"✅ 发现 pin: {pin}")
    else:
        print("❌ Cookie中没有 pin 字段！")
        return False
    
    # 检查3: 其他关键字段
    important_fields = ["pin", "unick", "jd_", "3AB9D23F7A4B3"]
    for field in important_fields:
        if field in COOKIE:
            print(f"✅ 包含 '{field}' 字段")
        else:
            print(f"⚠️  缺少 '{field}' 字段")
    
    # 检查4: 尝试简单请求
    print(f"\n{'='*80}")
    print(f"测试Cookie是否能访问API")
    print(f"{'='*80}\n")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": COOKIE,
        "Referer": "https://lives.jd.com"
    }
    
    try:
        # 测试直播列表API（不需要加密）
        url = "https://api.m.jd.com/api?functionId=predictLiveListToM&appid=live_pc&body={}&t=1"
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📥 测试请求状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ 能成功访问API，Cookie可能有效")
            try:
                data = response.json()
                if data.get("code") == 0 or data.get("code") == "0":
                    print(f"✅ API返回成功响应")
                    return True
                else:
                    print(f"⚠️  API返回错误: {data.get('msg', '未知错误')}")
                    return False
            except:
                print(f"⚠️  响应不是JSON格式")
        else:
            print(f"❌ API返回错误状态码: {response.status_code}")
            print(f"   响应体: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False
    
    print(f"\n{'='*80}")
    print("\n💡 如果以上测试都失败了，请按以下步骤更新Cookie:\n")
    print("1. 打开浏览器，访问 https://lives.jd.com")
    print("2. 确保已登录京东账号")
    print("3. 按 F12 打开开发者工具")
    print("4. 进入 Application > Cookies")
    print("5. 选择 lives.jd.com")
    print("6. 复制所有Cookie中的 Cookie 字符串（右键选择Copy all as cURL）")
    print("7. 更新 .env 文件中的 COOKIE 值")
    print("8. 重新运行测试")


if __name__ == "__main__":
    check_cookie_validity()
