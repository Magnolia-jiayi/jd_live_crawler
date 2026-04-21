"""
从浏览器截图中提取的URL进行分析
"""

# 从浏览器截图中的URL：
# https://api.m.jd.com/liveauth?functionId=liveauth&appid=live_pc&body=%7B%22content%22%3A%22tbV8seY199tCdw6GllmkW%2FosOzqSVpE6i4y3FoKHmtsjCjWmWoOtEaD%2FsqW0pwr2No6dCrcDRec9Ib5Jc570iyGJGzmd6bbsrQnNVqNmDvjXGjA3EJgV5ji2Si%2BkGtgFz3g3%2FXrV5Ym34nZLoE2K2OQyHcK7OnwbuBQGLBJLCrqxJxlMMd7akI%2FUzYLYghLQCepGs0ureT9T327PDZoXVXochBjunGtn9EjC4dtxVUKTZeAodjGZq8NGb0XP2qAX%22%2C+%22appId%22%3A+%22jd.mall%22%7D&t=1775914299714

from urllib.parse import unquote
import json
import base64

# 提取body参数
url_body_encoded = '%7B%22content%22%3A%22tbV8seY199tCdw6GllmkW%2FosOzqSVpE6i4y3FoKHmtsjCjWmWoOtEaD%2FsqW0pwr2No6dCrcDRec9Ib5Jc570iyGJGzmd6bbsrQnNVqNmDvjXGjA3EJgV5ji2Si%2BkGtgFz3g3%2FXrV5Ym34nZLoE2K2OQyHcK7OnwbuBQGLBJLCrqxJxlMMd7akI%2FUzYLYghLQCepGs0ureT9T327PDZoXVXochBjunGtn9EjC4dtxVUKTZeAodjGZq8NGb0XP2qAX%22%2C+%22appId%22%3A+%22jd.mall%22%7D'

# URL解码
body_decoded = unquote(url_body_encoded)
print("🔓 URL解码后的body:")
print(body_decoded)
print()

# 自动修正格式问题：去除所有+号
body_decoded_clean = body_decoded.replace('+', '')


# 解析JSON（使用去除+号后的字符串）
body_json = json.loads(body_decoded_clean)
print("📋 body JSON:")
print(json.dumps(body_json, indent=2))
print()

# 提取content（这是Base64编码的加密数据）
encrypted_content = body_json['content']
print(f"🔐 加密的content (Base64):")
print(encrypted_content)
print()

# 这个content是加密过的，我们无法直接看到里面的内容
# 但我们可以对比一下长度和格式


print(f"📊 content分析:")
print(f"   长度: {len(encrypted_content)} 字符")
# Base64自动补齐=号
padding = len(encrypted_content) % 4
if padding != 0:
    encrypted_content_padded = encrypted_content + ('=' * (4 - padding))
else:
    encrypted_content_padded = encrypted_content
try:
    decoded_bytes = base64.b64decode(encrypted_content_padded)
    print(f"   长度(解码后): {len(decoded_bytes)} 字节")
except Exception as e:
    print(f"   Base64解码失败: {e}")
print()

print("💡 关键发现:")
print("   浏览器中的content与我们生成的是相同的格式")
print("   都是Base64编码的加密数据")
print()

print("❓ 但为什么会'解密失败'？")
print("   可能是因为：")
print("   1. content中的原始数据（加密前）不同")
print("   2. 加密密钥不同")
print("   3. 加密方式不同")
print()

# 尝试对比我们生成的和浏览器实际发送的
our_content = "tbV8seY199tCdw6GllmkWyCNNENuGsgwLByA7svt5HbUchlkEVZXjAp20evnzxXbp+oohYcRbWKfpd/xyCmjNiz3YpO4ayl3Z+abo9pJLtdguOEw/RrL4aKC8oPV4Z7EURGKoMWWE1nmndXkeKgA5VaFZSzfwhV6Kqr48zNpkTg5HfMLbbkiYISQCvrMTdx2jT6AQAet322eZ9eNoibYQYxN606QWEKyCNXrE0KTUz0="

browser_content = encrypted_content

print(f"🔄 对比分析:")
print(f"   浏览器content长度: {len(browser_content)}")
print(f"   我们的content长度: {len(our_content)}")
print()

if browser_content[:50] == our_content[:50]:
    print("   ✅ 前50个字符相同")
else:
    print("   ❌ 前50个字符不同!")
    print(f"      浏览器: {browser_content[:50]}")
    print(f"      我们的: {our_content[:50]}")
print()

print("🎯 下一步需要调查:")
print("   • content中可能包含的原始数据结构是什么")
print("   • 是否所有字段都被正确加密了")
print("   • 是否需要其他的加密参数或字段")
