"""
使用Selenium在真实浏览器中进行鉴权请求
"""
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_auth_via_selenium(live_id: str):
    """
    使用Selenium在浏览器中进行鉴权请求
    """
    
    print(f"\n{'='*80}")
    print(f"🌐 使用Selenium在真实浏览器中获取鉴权")
    print(f"{'='*80}\n")
    
    # 配置Chrome选项
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # 如果需要后台运行，取消注释
    chrome_options.add_argument("--start-maximized")
    # 使用真实的Chrome用户数据目录，保持登录状态
    chrome_options.add_argument(
        r"--user-data-dir=C:\Users\ASUS\AppData\Local\Google\Chrome\User Data"
    )
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # 第一步：访问直播页面
        print(f"1️⃣  打开直播页面...")
        driver.get("https://zhibo.jd.com/")
        
        # 等待页面加载
        time.sleep(3)
        
        # 第二步：在Console中直接执行鉴权请求
        print(f"2️⃣  在浏览器Console中执行鉴权请求...")
        

        # 注入JS，hook住加密函数，自动打印content明文

        js_hook = '''
        (function deepHookAllAES(obj, path, visited) {
            if (!obj || typeof obj !== 'object' && typeof obj !== 'function') return;
            if (!visited) visited = new Set();
            if (visited.has(obj)) return;
            visited.add(obj);
            try {
                for (let k in obj) {
                    if (!obj.hasOwnProperty(k)) continue;
                    let val;
                    try { val = obj[k]; } catch(e) { continue; }
                    if (typeof val === 'function') {
                        let code = val.toString();
                        if (/AES|encrypt|Encrypt|加密/.test(code)) {
                            if (!val.__isHooked) {
                                let orig = val;
                                obj[k] = function() {
                                    try {
                                        console.log('【HOOK到加密前明文】', arguments[0], 'at', path+'.'+k);
                                    } catch(e){}
                                    return orig.apply(this, arguments);
                                }
                                obj[k].__isHooked = true;
                                console.log('【HOOK已注入】', path+'.'+k);
                            }
                        }
                    }
                    if (typeof val === 'object' || typeof val === 'function') {
                        deepHookAllAES(val, path+'.'+k, visited);
                    }
                }
            } catch(e){}
        })(window, 'window');
        '''
        driver.execute_script(js_hook)
        print("   已递归注入全局加密明文HOOK，请在Console中查找【HOOK到加密前明文】日志！")

        # 继续执行原有鉴权请求
        js_code = f"""
        (async function() {{
            try {{
                const response = await fetch('https://api.m.jd.com/liveauth?functionId=liveauth&appid=live_pc&body=%7B%22content%22:%22加密content%22,%22appId%22:%22jd.mall%22%7D&t=' + Date.now(), {{
                    method: 'POST',
                    headers: {{
                        'Accept': 'application/json, text/plain, */*',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Origin': 'https://zhibo.jd.com',
                        'Referer': 'https://zhibo.jd.com/',
                        'Sec-Fetch-Dest': 'empty',
                        'Sec-Fetch-Mode': 'cors',
                        'Sec-Fetch-Site': 'same-site',
                        'Priority': 'u=1, i'
                    }},
                    credentials: 'include'
                }});
                const data = await response.json();
                console.log('AUTH_RESPONSE:', JSON.stringify(data));
                return data;
            }} catch (error) {{
                console.error('AUTH_ERROR:', error.message);
                return {{ error: error.message }};
            }}
        }})();
        """
        result = driver.execute_script(js_code)
        print(f"   执行结果: {result}")

        # 等待用户查看Console输出
        time.sleep(2)
        
        # 第三步：获取浏览器的Network日志（如果可用）
        print(f"\n3️⃣  获取浏览器性能日志...")
        
        try:
            logs = driver.get_log('performance')
            auth_requests = []
            
            for log in logs:
                message = json.loads(log['message'])
                if 'liveauth' in str(message):
                    auth_requests.append(message)
            
            if auth_requests:
                print(f"   ✅ 找到 {len(auth_requests)} 个liveauth请求")
                for req in auth_requests[:1]:  # 只显示第一个
                    print(f"   Details: {json.dumps(req, indent=2)[:200]}")
            else:
                print(f"   ⚠️ 未找到liveauth请求日志")
        except Exception as e:
            print(f"   ⚠️ 无法获取性能日志: {e}")
        
        print(f"\n✅ Selenium测试完成")
        print(f"\n💡 请在打开的浏览器Console中检查是否看到 AUTH_RESPONSE 或 AUTH_ERROR")
        print(f"   按 F12 > Console 查看")
        
        input("按Enter键关闭浏览器...")
        
    except Exception as e:
        print(f"❌ Selenium异常: {e}")
    
    finally:
        if driver:
            driver.quit()


def print_selenium_guide():
    """打印关于如何使用此脚本的指南"""
    guide = """
═══════════════════════════════════════════════════════════════════════════════
📖 Selenium脚本使用指南
═══════════════════════════════════════════════════════════════════════════════

此脚本使用Selenium在真实的Chrome浏览器中进行鉴权请求。

准备工作：
  1. 确保Chrome浏览器已安装
  2. 确保已登录京东账号（脚本会使用您的登录状态）
  3. 确保WebDriver与Chrome版本匹配

运行方式：
  python use_selenium_auth.py

脚本流程：
  1. 打开真实的Chrome浏览器
  2. 访问 https://zhibo.jd.com/
  3. 在浏览器Console中执行鉴权请求
  4. 显示响应结果
  5. 等待您按Enter关闭浏览器

优势：
  ✓ 使用真实的浏览器环境
  ✓ 继承所有的Cookie和登录状态
  ✓ 浏览器会自动处理CORS
  ✓ 可以看到完整的请求/响应

═══════════════════════════════════════════════════════════════════════════════
"""
    print(guide)


if __name__ == "__main__":
    print_selenium_guide()
    
    # 运行脚本
    live_id = "44756937"  # 测试直播间
    get_auth_via_selenium(live_id)
