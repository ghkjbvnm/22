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
    """
    Selenium管理器类
    用于管理浏览器驱动和页面实例的创建与管理
    """
    def __init__(self):
        """
        初始化SeleniumManager
        contexts: 存储浏览器窗口/标签的字典
        pages: 存储页面实例的嵌套字典
        """
        self.driver = None
        self.contexts = {}
        self.pages = {}

    def get_context(self, context_id):
        """
        获取或创建浏览器窗口
        Args:
            context_id: 上下文标识符
        Returns:
            webdriver实例
        """
        if context_id in self.contexts:
            return self.contexts[context_id]
        else:
            self.contexts[context_id] = self.driver
            return self.contexts[context_id]

    def get_page(self, context_id, page_id):
        """
        获取或创建页面实例（新标签页）
        Args:
            context_id: 上下文标识符
            page_id: 页面标识符
        Returns:
            webdriver实例
        """
        driver = self.get_context(context_id)
        if context_id not in self.pages:
            self.pages[context_id] = {}
        if page_id in self.pages[context_id]:
            # 切换到已存在的窗口/标签页
            self.pages[context_id][page_id].switch_to.window(self.pages[context_id][page_id].current_window_handle)
            return self.pages[context_id][page_id]
        else:
            # 创建新的标签页
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

        self.driver = webdriver.Chrome(options=chrome_options)
        self.contexts["default"] = self.driver

    def connect_to_browser(self, debugger_port, webdriver_path=None):
        """
        连接到已有的浏览器实例（通过远程调试端口）
        Args:
            debugger_port: 远程调试端口
            webdriver_path: chromedriver的路径（可选）
        """
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", f"localhost:{debugger_port}")

        if webdriver_path:
            service = Service(executable_path=webdriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)
        self.contexts["default"] = self.driver

    def close_browser(self):
        """关闭浏览器实例"""
        if self.driver:
            self.driver.quit()


def main():
    """
    主函数：演示如何使用SeleniumManager进行浏览器自动化
    包含API调用启动浏览器、连接CDP、页面操作等功能
    """
    # 初始化管理器
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

    # 检查启动是否成功
    if not response_data.get("success"):
        print("启动浏览器失败")
        return

    # 获取调试端口和webdriver路径
    debugging_port = response_data.get("data", {}).get("debuggingPort")
    webdriver_path = response_data.get("data", {}).get("webdriver_path")
    if not debugging_port:
        print("未找到调试端口")
        return

    print(f"准备连接浏览器 - 端口: {debugging_port}, 驱动路径: {webdriver_path}")

    # 使用Selenium连接到浏览器
    try:
        manager.connect_to_browser(debugging_port, webdriver_path)
        print("成功连接到浏览器")

        # 获取driver实例
        driver = manager.driver

        # 管理浏览器上下文和页面
        if len(driver.window_handles) > 0:
            # 使用已存在的窗口
            driver.switch_to.window(driver.window_handles[0])
            manager.contexts["default"] = driver
            if "default" not in manager.pages:
                manager.pages["default"] = {}
            manager.pages["default"]["main"] = driver
        else:
            # 创建新的上下文和页面
            manager.launch_browser()
            driver = manager.get_context("default")
            driver = manager.get_page("default", "main")

        # 演示：访问百度首页
        driver.get("https://www.baidu.com")

        # 等待页面加载完成
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "kw"))
        )
        print("页面加载成功")

        # 在这里可以添加更多的自动化测试代码
        # 例如：页面交互、数据抓取等

        time.sleep(2)  # 演示延迟

    except Exception as err:
        print(f"Selenium操作出错: {err}")
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
            if not stop_response_data.get("success"):
                print("通过API关闭浏览器失败")
        except Exception as err:
            print(f"关闭浏览器时出错: {err}")

        # 关闭Selenium连接
        manager.close_browser()


# 运行主函数
if __name__ == "__main__":
    main()
