import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests


class SeleniumManager:
    """Selenium管理器类 - 支持绕过Cloudflare检测"""

    def __init__(self):
        self.driver = None
        self.contexts = {}
        self.pages = {}

    def get_context(self, context_id):
        if context_id in self.contexts:
            return self.contexts[context_id]
        else:
            self.contexts[context_id] = self.driver
            return self.contexts[context_id]

    def get_page(self, context_id, page_id):
        driver = self.get_context(context_id)
        if context_id not in self.pages:
            self.pages[context_id] = {}
        if page_id in self.pages[context_id]:
            driver.switch_to.window(driver.current_window_handle)
            return self.pages[context_id][page_id]
        else:
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            self.pages[context_id][page_id] = driver
            return self.pages[context_id][page_id]

    def launch_browser(self, headless=False):
        """
        启动浏览器实例
        Args:
            headless: 是否无头模式
        """
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')

        # 添加反检测参数（移除不支持的选项）
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.contexts["default"] = self.driver

    def connect_to_browser(self, debugger_port, webdriver_path=None):
        """
        连接到已有的浏览器实例
        Args:
            debugger_port: 远程调试端口
            webdriver_path: chromedriver路径
        """
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", f"localhost:{debugger_port}")

        # 移除不支持的选项，只保留基本的反检测参数
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')

        if webdriver_path:
            service = Service(executable_path=webdriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)

        self.contexts["default"] = self.driver

    def close_browser(self):
        if self.driver:
            self.driver.quit()


def main():
    """主函数：演示如何绕过Cloudflare检测"""
    manager = SeleniumManager()

    # API配置
    BASE_URL = "http://localhost:9000"
    data = {"id": 1}
    headers = {
        "Content-Type": "application/json",
        "api-key": "WGb9tYs132FafT0373dUpCvDjBxfCCD3"
    }

    # 通过API启动浏览器环境
    try:
        response = requests.post(
            f"{BASE_URL}/api/launchBrowser",
            headers=headers,
            data=json.dumps(data)
        )
        response_data = response.json()
        print("启动浏览器响应:", response_data)
    except Exception as err:
        print(f"启动浏览器失败: {err}")
        return

    if not response_data.get("success"):
        print("启动浏览器失败")
        return

    debugging_port = response_data.get("data", {}).get("debuggingPort")
    webdriver_path = response_data.get("data", {}).get("webdriver_path")

    print(f"准备连接浏览器 - 端口: {debugging_port}, 驱动路径: {webdriver_path}")

    try:
        manager.connect_to_browser(debugging_port, webdriver_path)
        print("成功连接到浏览器")

        driver = manager.driver

        # 添加更多反检测配置（可选）
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });
            '''
        })

        if len(driver.window_handles) > 0:
            driver.switch_to.window(driver.window_handles[0])
            manager.contexts["default"] = driver
            if "default" not in manager.pages:
                manager.pages["default"] = {}
            manager.pages["default"]["main"] = driver

        # 访问目标网站（可能有Cloudflare保护）
        print("正在访问网站...")
        driver.get("https://www.overchargedforbeef.com/en/Claim")

        # # 等待页面加载完成，增加等待时间应对Cloudflare验证
        # try:
        #     WebDriverWait(driver, 50).until(
        #         EC.presence_of_element_located((By.ID, "kw"))
        #     )
        #     print("页面加载成功！")
        # except:
        #     print("等待超时，但页面可能已加载")

        # 等待额外的Cloudflare验证时间
        time.sleep(30)

        # 检查是否有Cloudflare验证页面
        try:
            cf_challenge = driver.find_elements(By.CSS_SELECTOR, "#challenge-form, .cf-challenge-running")
            if cf_challenge:
                print("检测到Cloudflare验证，等待验证完成...")
                # 等待Cloudflare验证完成（最多60秒）
                for i in range(60):
                    time.sleep(1)
                    cf_challenge = driver.find_elements(By.CSS_SELECTOR, "#challenge-form, .cf-challenge-running")
                    if not cf_challenge:
                        print("Cloudflare验证通过！")
                        break
                    if i % 10 == 0:
                        print(f"等待Cloudflare验证... ({i+1}s)")
        except Exception as e:
            print(f"检查Cloudflare验证时出错: {e}")

        time.sleep(2)

    except Exception as err:
        print(f"Selenium操作出错: {err}")
        import traceback
        traceback.print_exc()
    finally:
        # 通过API关闭浏览器
        try:
            stop_response = requests.post(
                f"{BASE_URL}/api/stopBrowser",
                headers=headers,
                data=json.dumps(data)
            )
            stop_response_data = stop_response.json()
            print("关闭浏览器响应:", stop_response_data)
        except Exception as err:
            print(f"关闭浏览器时出错: {err}")

        manager.close_browser()


if __name__ == "__main__":
    main()
