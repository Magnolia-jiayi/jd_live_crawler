"""
完整的浏览器请求数据收集模板
"""


template = {
  "description": "从浏览器Network中复制的liveauth请求的完整信息",
  "notes": [
    "1. 在浏览器中打开 Network 标签页",
    "2. 找到 functionId=liveauth 的POST请求",
    "3. 右键 Copy as cURL，然后粘贴到 curl_command 字段",
    "4. 也可以逐字段复制下列信息"
  ],
  "curl_command_example": "curl -X POST 'https://api.m.jd.com/liveauth?...' -H 'Cookie: ...' -H 'User-Agent: ...'",
  "request": {
    "method": "POST",
    "url": "https://api.m.jd.com/liveauth",
    "full_url_with_params": "请从浏览器Network的Headers标签中复制完整的Request URL",
    "query_parameters": {
      "functionId": "liveauth",
      "appid": "live_pc",
      "body": "这里是URL编码的JSON内容，包含加密的content",
      "t": "时间戳"
    },
    "request_headers": {
      ":method": "POST",
      ":path": "从浏览器Headers标签的:path字段复制",
      ":scheme": "https",
      ":authority": "api.m.jd.com",
      "accept": "application/json, text/plain, */*",
      "accept-encoding": "gzip, deflate, br, zstd",
      "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
      "cookie": "这里是完整的Cookie值，确保包含所有分号分隔的字段",
      "content-length": "0",
      "origin": "https://zhibo.jd.com",
      "priority": "u=1, i",
      "referer": "https://zhibo.jd.com/",
      "sec-ch-ua": "浏览器会自动发送",
      "sec-ch-ua-mobile": "?0",
      "sec-ch-ua-platform": "\"Windows\"",
      "sec-fetch-dest": "empty",
      "sec-fetch-mode": "cors",
      "sec-fetch-site": "same-site",
      "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      "其他请求头": "如果浏览器发送了其他特殊的header，也请复制这里"
    }
  },
  "response": {
    "status_code": 200,
    "headers": {
      "access-control-allow-credentials": "true",
      "access-control-allow-origin": "https://zhibo.jd.com",
      "content-type": "application/json",
      "其他响应头": "所有响应头"
    },
    "body": {
      "code": "响应的code字段值",
      "msg": "或message字段",
      "data": "包含token和WebSocket URL的数据结构"
    }
  },
  "important_observations": {
    "observation_1": "请求是否发送了request body？Content-Length是否为0？",
    "observation_2": "body参数中的content是否看起来像Base64编码的加密数据？",
    "observation_3": "浏览器是否发送了任何特殊的验证token或signature？",
    "observation_4": "Response中是否包含user-id、session-id或其他tracking参数？",
    "observation_5": "浏览器请求成功(200)的关键是什么？"
  }
}

import json
print(json.dumps(template, indent=2, ensure_ascii=False))

# 保存到文件
with open("browser_request_template.json", "w", encoding="utf-8") as f:
    json.dump(template, f, indent=2, ensure_ascii=False)

print("\n✅ 模板已保存到 browser_request_template.json")
print("\n💡 请按照模板填写浏览器请求的完整信息，然后分享给我分析")
