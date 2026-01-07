import asyncio
import json
import requests
from playwright.async_api import async_playwright


class PlaywrightManager:
    """
    Playwright管理器类
    用于管理浏览器上下文和页面实例的创建与管理
    """
    def __init__(self):
        """
        初始化PlaywrightManager
        contexts: 存储浏览器上下文的字典
        pages: 存储页面实例的嵌套字典
        """
        self.contexts = {}
        self.pages = {}

    async def get_context(self, context_id):
        """
        获取或创建浏览器上下文
        Args:
            context_id: 上下文标识符
        Returns:
            browser context实例
        """
        if context_id in self.contexts:
            return self.contexts[context_id]
        else:
            context = await self.browser.new_context()
            self.contexts[context_id] = context
            return context

    async def get_page(self, context_id, page_id):
        """
        获取或创建页面实例
        Args:
            context_id: 上下文标识符
            page_id: 页面标识符
        Returns:
            page实例
        """
        context = await self.get_context(context_id)
        if context_id not in self.pages:
            self.pages[context_id] = {}
        if page_id in self.pages[context_id]:
            return self.pages[context_id][page_id]
        else:
            page = await context.new_page()
            self.pages[context_id][page_id] = page
            return page

    async def launch_browser(self):
        """启动浏览器实例"""
        async with async_playwright() as p:
            self.browser = await p.chromium.launch(headless=False)

    async def close_browser(self):
        """关闭浏览器实例"""
        await self.browser.close()


async def main():
    """
    主函数：演示如何使用PlaywrightManager进行浏览器自动化
    包含API调用启动浏览器、连接CDP、页面操作等功能
    """
    # 初始化管理器
    manager = PlaywrightManager()
    await manager.launch_browser()

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

    # 获取调试端口
    debugging_port = response_data.get("data", {}).get("debuggingPort")
    if not debugging_port:
        print("未找到调试端口")
        return

    # 使用Playwright连接到浏览器
    async with async_playwright() as p:
        # 通过CDP协议连接到浏览器
        manager.browser = await p.chromium.connect_over_cdp(
            f"http://localhost:{debugging_port}"
        )

        # 管理浏览器上下文和页面
        contexts = manager.browser.contexts
        if contexts:
            # 使用已存在的上下文
            context = contexts[0]
            manager.contexts["default"] = context
            page = await context.new_page()
            if "default" not in manager.pages:
                manager.pages["default"] = {}
            manager.pages["default"]["main"] = page
        else:
            # 创建新的上下文和页面
            context = await manager.get_context("default")
            page = await manager.get_page("default", "main")

        # 演示：访问百度首页
        await page.goto("https://www.baidu.com")

        # 在这里可以添加更多的自动化测试代码
        # 例如：页面交互、数据抓取等

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


# 运行主函数
if __name__ == "__main__":
    asyncio.run(main())