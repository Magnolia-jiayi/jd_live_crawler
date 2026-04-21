"""
自动化比对：浏览器抓包与代码生成的auth content字段
"""
import json
import base64
from urllib.parse import unquote
from api_client import JDLiveAPIClient

# 1. 粘贴浏览器抓包的body参数
browser_body_encoded = '%7B%22content%22%3A%22tbV8seY199tCdw6GllmkW%2FosOzqSVpE6i4y3FoKHmtsjCjWmWoOtEaD%2FsqW0pwr2No6dCrcDRec9Ib5Jc570iyGJGzmd6bbsrQnNVqNmDvjXGjA3EJgV5ji2Si%2BkGtgFz3g3%2FXrV5Ym34nZLoE2K2OQyHcK7OnwbuBQGLBJLCrqxJxlMMd7akI%2FUzYLYghLQCepGs0ureT9T327PDZoXVXochBjunGtn9EjC4dtxVUKTZeAodjGZq8NGb0XP2qAX%22%2C+%22appId%22%3A+%22jd.mall%22%7D'

# 2. 解码浏览器body
browser_body_decoded = unquote(browser_body_encoded).replace('+', '')
browser_body_json = json.loads(browser_body_decoded)
browser_content = browser_body_json['content']

# 3. 自动补齐Base64
padding = len(browser_content) % 4
if padding != 0:
    browser_content_padded = browser_content + ('=' * (4 - padding))
else:
    browser_content_padded = browser_content
browser_content_bytes = base64.b64decode(browser_content_padded)

print("【浏览器content】长度:", len(browser_content))
print("【浏览器content】解码后字节:", len(browser_content_bytes))

# 4. 生成一份代码端的content
client = JDLiveAPIClient()
live_id = '44756937'  # 可根据实际情况调整
# 生成与浏览器结构一致的content
content = {
    "appId": "jd.mall",
    "clientType": "m",
    "pin": client.pin,
    "eid": client.get_jd_eid() or "",
    "groupId": live_id,
    "timestamp": 1712774400000,  # 固定时间戳，便于比对
    "random": "abcdef"           # 固定随机串，便于比对
}
our_content = client.encrypt_content(content)

# 5. 自动补齐Base64
padding2 = len(our_content) % 4
if padding2 != 0:
    our_content_padded = our_content + ('=' * (4 - padding2))
else:
    our_content_padded = our_content
our_content_bytes = base64.b64decode(our_content_padded)

print("【代码content】长度:", len(our_content))
print("【代码content】解码后字节:", len(our_content_bytes))

# 6. 自动化比对
print("\n==== 自动化比对结果 ====")
if browser_content == our_content:
    print("✅ Base64字符串完全一致")
else:
    print("❌ Base64字符串不一致")
    # 前50字符对比
    print("浏览器:", browser_content[:50])
    print("代码  :", our_content[:50])
    # 解码后字节对比
    if browser_content_bytes == our_content_bytes:
        print("✅ 解码后字节流一致")
    else:
        print("❌ 解码后字节流不一致")
        # 输出前20字节
        print("浏览器:", browser_content_bytes[:20])
        print("代码  :", our_content_bytes[:20])

# 7. 比对加密前的原始JSON
print("\n==== 加密前原始JSON对比 ====")
print("浏览器:")
print(json.dumps({
    "appId": "jd.mall",
    # 其他字段未知，需人工补充
}, ensure_ascii=False, indent=2))
print("代码:")
print(json.dumps(content, ensure_ascii=False, indent=2))

print("\n提示：如需进一步比对，请补充浏览器端加密前的原始JSON结构！")
