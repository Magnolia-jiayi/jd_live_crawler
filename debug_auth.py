"""
调试脚本 - 使用Selenium捕获真实的鉴权请求
"""
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
logger = logging.getLogger(__name__)


def debug_auth_request():
    """
    使用Selenium打开京东直播页面并捕获鉴权请求
    """
    
    # 配置Chrome选项
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # 取消注释以在后台运行
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument(f"user-data-dir=C:\\Users\\ASUS\\AppData\\Local\\Google\\Chrome\\User Data")  # 使用真实Cookie
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        logger.info("🔍 打开京东直播页面...")
        driver.get("https://lives.jd.com")
        
        # 等待页面加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "live-item"))
        )
        
        logger.info("✅ 页面加载完成")
        
        # 获取浏览器日志（包括网络请求）
        logger.info("\n📊 捕获的网络请求：")
        logger.info("=" * 80)
        
        # 使用Performance API获取请求信息
        performance_logs = driver.get_log('performance')
        
        for log in performance_logs:
            try:
                message = json.loads(log['message'])
                method = message.get('message', {}).get('method', '')
                
                # 查找Network请求
                if method == 'Network.responseReceived':
                    request_details = message.get('message', {}).get('params', {})
                    response = request_details.get('response', {})
                    url = response.get('url', '')
                    
                    # 寻找liveauth请求
                    if 'liveauth' in url or 'functionId=liveauth' in url:
                        logger.info(f"\n🎯 找到鉴权请求！")
                        logger.info(f"URL: {url}")
                        logger.info(f"状态码: {response.get('status')}")
                        logger.info(f"Headers: {json.dumps(response.get('headers', {}), indent=2, ensure_ascii=False)}")
                        
            except Exception as e:
                pass
        
        # 另一种方法：直接检查浏览器console中的fetch/XHR请求
        logger.info("\n" + "=" * 80)
        logger.info("💡 手动检查方法：")
        logger.info("1. 在浏览器中按F12打开开发者工具")
        logger.info("2. 进入Network标签")
        logger.info("3. 在Filter中输入'liveauth'")
        logger.info("4. 刷新页面或操作页面触发请求")
        logger.info("5. 点击请求查看详细信息")
        logger.info("6. 将以下信息复制到debugged_requests.json文件中：")
        logger.info("   - Request URL")
        logger.info("   - Request Headers (全部)")
        logger.info("   - Request Body")
        logger.info("   - Response Status")
        logger.info("   - Response Body")
        logger.info("\n按任意键继续...")
        input()
        
    finally:
        driver.quit()
        logger.info("✅ 浏览器已关闭")


if __name__ == "__main__":
    debug_auth_request()
