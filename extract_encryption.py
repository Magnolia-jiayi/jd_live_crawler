"""
从浏览器中提取加密逻辑和密钥
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import json


def extract_encryption_logic():
    """
    从浏览器中提取加密逻辑和密钥
    """
    
    print(f"\n{'='*80}")
    print(f"🔐 从浏览器JavaScript中提取加密逻辑")
    print(f"{'='*80}\n")
    
    chrome_options = Options()
    chrome_options.add_argument(
        r"--user-data-dir=C:\Users\ASUS\AppData\Local\Google\Chrome\User Data"
    )
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        print("1️⃣  打开直播页面...")
        driver.get("https://zhibo.jd.com/")
        time.sleep(3)
        
        print("2️⃣  检查JavaScript中的加密密钥...")
        
        # 尝试找到加密密钥和方法
        js_code = """
        (function() {
            let results = {
                keys_found: [],
                encryption_info: {}
            };
            
            // 搜索可能的加密密钥
            const key_patterns = [
                'RYm2dMPMWD9AxYFk',
                '0102030405060708',
                'secretKey',
                'encryptKey',
                'aesKey',
                'iv'
            ];
            
            // 检查window对象
            for (let key in window) {
                try {
                    let value = window[key];
                    if (typeof value === 'string' && value.length > 10) {
                        for (let pattern of key_patterns) {
                            if (value.includes(pattern) || key.toLowerCase().includes('encrypt') || key.toLowerCase().includes('key')) {
                                results.keys_found.push({
                                    'window_key': key,
                                    'contains': pattern
                                });
                            }
                        }
                    }
                } catch (e) {}
            }
            
            // 检查localStorage
            try {
                for (let i = 0; i < localStorage.length; i++) {
                    let key = localStorage.key(i);
                    let value = localStorage.getItem(key);
                    if (value && (value.includes('RYm2') || value.includes('aes') || value.includes('encrypt'))) {
                        results.localStorage = {
                            [key]: value.substring(0, 100)
                        };
                    }
                }
            } catch (e) {}
            
            // 检查sessionStorage
            try {
                for (let i = 0; i < sessionStorage.length; i++) {
                    let key = sessionStorage.key(i);
                    let value = sessionStorage.getItem(key);
                    if (value && (value.includes('RYm2') || value.includes('aes') || value.includes('encrypt'))) {
                        results.sessionStorage = {
                            [key]: value.substring(0, 100)
                        };
                    }
                }
            } catch (e) {}
            
            // 尝试找到加密函数
            console.log('ENCRYPTION_INFO:', JSON.stringify(results, null, 2));
            return results;
        })();
        """
        
        result = driver.execute_script(js_code)
        print(f"\n📋 提取结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 第二步：尝试查看浏览器Network中实际发送的请求
        print(f"\n3️⃣  分析Network中的实际请求...")
        
        # 获取performance logs
        logs = driver.get_log('performance')
        
        auth_requests = []
        for log in logs:
            try:
                msg = json.loads(log['message'])
                if 'liveauth' in str(msg):
                    auth_requests.append(msg)
            except:
                pass
        
        if auth_requests:
            print(f"\n   ✅ 找到 {len(auth_requests)} 个liveauth请求")
            print(f"   (详细信息已显示在浏览器Console中)")
        
        print(f"\n4️⃣  建议排查项：")
        print(f"   • content中可能需要的其他字段")
        print(f"   • 加密密钥是否硬编码在JavaScript中")
        print(f"   • 是否需要签名或hash")
        print(f"   • 是否需要设备指纹或其他参数")
        
        input("\n按Enter键继续检查浏览器Console...")
        
        # 尝试在页面中注入更深入的分析代码
        print(f"\n5️⃣  尝试hook加密过程...")
        
        hook_code = """
        // 保存原始fetch
        const originalFetch = window.fetch;
        
        window.fetch = function(...args) {
            const [resource, config] = args;
            
            if (resource && resource.includes('liveauth')) {
                console.log('🔍 LIVEAUTH REQUEST INTERCEPTED');
                console.log('URL:', resource);
                if (config && config.body) {
                    console.log('BODY:', config.body);
                }
            }
            
            return originalFetch.apply(this, args);
        };
        
        console.log('✅ Fetch已被hook，现在进行请求会被记录');
        """
        
        driver.execute_script(hook_code)
        
        print(f"   ✅ Fetch hook已安装")
        print(f"   现在进行鉴权请求会被拦截并打印到Console")
        
        input("\n按任意键关闭浏览器...")
        
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    extract_encryption_logic()
