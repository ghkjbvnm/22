import requests
import json

class VirtualBrowserManager:
    def __init__(self, base_url, api_key):
        """
        初始化虚拟浏览器管理器
        :param base_url: API基础地址（如http://localhost:8080）
        :param api_key: 认证密钥（2.1.5+版本必填）
        """
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "api-key": api_key
        }

    def create_browser(self, name, group="默认分组", **kwargs):
        """
        创建浏览器环境
        :param name: 环境名称
        :param group: 分组名称（默认"默认分组"）
        :param kwargs: 其他可选参数（如proxy、homepage等）
        :return: 响应结果字典
        """
        url = f"{self.base_url}/api/addBrowser"
        data = {
            "name": name,
            "group": [group],
            "screen": {
                "mode": 1,  # 1=自定义分辨率，1=1920x1080，2=1366x768，3=1280x720
                "width": 800,
                "height": 600,
                "_value": "1920 x 1080"
        },
            **kwargs
        }
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        return response.json()

    def open_browser(self, browser_id):
        """
        打开浏览器环境
        :param browser_id: 环境ID
        :return: 响应结果字典
        """
        url = f"{self.base_url}/api/launchBrowser"
        data = {"id": browser_id}
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        return response.json()

    def close_browser(self, browser_id):
        """
        关闭浏览器环境
        :param browser_id: 环境ID
        :return: 响应结果字典
        """
        url = f"{self.base_url}/api/stopBrowser"
        data = {"id": browser_id}
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        return response.json()

    def delete_browser(self, browser_id):
        """
        删除浏览器环境
        :param browser_id: 环境ID
        :return: 响应结果字典
        """
        url = f"{self.base_url}/api/deleteBrowser"
        data = {"id": browser_id}
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        return response.json()

    def get_browser_list(self, group=None, name=None, remark=None):
        """
        获取环境列表（用于验证操作结果）
        :param group: 按分组筛选
        :param name: 按名称筛选
        :return: 环境列表数据
        """
        url = f"{self.base_url}/api/getBrowserList"
        params = {}
        if group:
            params["group"] = group
        if name:
            params["name"] = name
        if remark:
            params["remark"] = remark
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()


# 使用示例
if __name__ == "__main__":
    with open('API_KEY.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    api_key = data['API_KEY']
    # 配置API地址和密钥
    BASE_URL = "http://localhost:9000"  # 替换为实际地址
    API_KEY = api_key           # 替换为实际密钥

    # 初始化管理器
    manager = VirtualBrowserManager(BASE_URL, API_KEY)

    try:
        # 1. 创建环境
        # create_result = manager.create_browser(
        #     name="测试环境",
        #     group="测试分组",
        #     homepage={"mode": 1, "value": "https://www.baidu.com"}  # 自定义首页
        # )
        # if create_result["success"]:
        #     browser_id = create_result["data"]["id"]
        #     print(f"创建成功，环境ID：{browser_id}")

            # 2. 打开环境
            open_result = manager.open_browser("2")
            print("打开环境结果：", "成功" if open_result["success"] else "失败")

            # 3. 关闭环境
            # close_result = manager.close_browser(browser_id)
            # print("关闭环境结果：", "成功" if close_result["success"] else "失败")

        # 4. 删除环境（如需测试请取消注释）
        # delete_result = manager.delete_browser(browser_id)
        # print("删除环境结果：", "成功" if delete_result["success"] else "失败")

        # 查看环境列表
        # print("\n当前环境列表：")
        # print(json.dumps(manager.get_browser_list(), indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"操作失败：{str(e)}")