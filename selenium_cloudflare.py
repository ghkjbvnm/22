import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import pandas as pd


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
    headers = {
        "Content-Type": "application/json",
        "api-key": "WSgRVGQPv9WsDSrhEWy2eDCtLPakbeg4"
    }

    # 步骤1: 创建浏览器环境
    print("步骤1: 创建浏览器环境...")
    create_browser_data = {
        "name": "环境2",
      
    }

    try:
        create_response = requests.post(
            f"{BASE_URL}/api/addBrowser",
            headers=headers,
            data=json.dumps(create_browser_data)
        )
        create_response_data = create_response.json()
        print("创建浏览器响应:", create_response_data)

        if not create_response_data.get("success"):
            print("创建浏览器失败")
            return

        browser_id = create_response_data.get("data", {}).get("id")
        print(f"✓ 浏览器环境创建成功，ID: {browser_id}")

    except Exception as err:
        print(f"创建浏览器失败: {err}")
        return

    # 步骤2: 启动浏览器
    print("\n步骤2: 启动浏览器...")
    launch_data = {"id": browser_id}

    try:
        launch_response = requests.post(
            f"{BASE_URL}/api/launchBrowser",
            headers=headers,
            data=json.dumps(launch_data)
        )
        launch_response_data = launch_response.json()
        print("启动浏览器响应:", launch_response_data)
    except Exception as err:
        print(f"启动浏览器失败: {err}")
        return

    if not launch_response_data.get("success"):
        print("启动浏览器失败")
        return

    debugging_port = launch_response_data.get("data", {}).get("debuggingPort")
    webdriver_path = launch_response_data.get("data", {}).get("webdriver_path")

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

        # 读取Excel表格数据
        print("读取Excel表格...")
        df = pd.read_excel('填表信息.xlsx', sheet_name='Sheet1')

        # 遍历每一行数据进行填写
        for index, row in df.iterrows():
            print(f"\n正在填写第 {index + 1} 行数据...")

            # 点击 ClaimantType
            try:
                claimant_type = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="ClaimantType"]'))
                )
                claimant_type.click()
                print("✓ 点击 ClaimantType")
                time.sleep(0.5)
            except Exception as e:
                print(f"点击 ClaimantType 失败: {e}")


            time.sleep(2)

            # 输入名
            try:
                first_name = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="FirstName"]'))
                )
                first_name.clear()
                first_name.send_keys(str(row['名']))
                print(f"✓ 输入名: {row['名']}")
                time.sleep(0.5)
            except Exception as e:
                print(f"输入名失败: {e}")

            # 输入姓
            try:
                last_name = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="LastName"]'))
                )
                last_name.clear()
                last_name.send_keys(str(row['姓']))
                print(f"✓ 输入姓: {row['姓']}")
                time.sleep(0.5)
            except Exception as e:
                print(f"输入姓失败: {e}")

            # 输入地址第一行
            try:
                address1 = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="Address_Address1"]'))
                )
                address1.clear()
                address1.send_keys(str(row['地址第一行']))
                print(f"✓ 输入地址第一行: {row['地址第一行']}")
                time.sleep(0.5)
            except Exception as e:
                print(f"输入地址第一行失败: {e}")

            # 输入城市
            try:
                city = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="Address_City"]'))
                )
                city.clear()
                city.send_keys(str(row['城市']))
                print(f"✓ 输入城市: {row['城市']}")
                time.sleep(0.5)
            except Exception as e:
                print(f"输入城市失败: {e}")

            # 点击州下拉框
            try:
                state_dropdown = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="Address_State"]'))
                )
                state_dropdown.click()
                print("✓ 点击 Address_State 下拉框")
                time.sleep(1)
            except Exception as e:
                print(f"点击州下拉框失败: {e}")

            # 选择州（使用州全名）
            try:
                state_name = str(row['州全名'])
                state_option = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f'//*[@id="Address_State"]/option[text()="{state_name}"]'))
                )
                state_option.click()
                print(f"✓ 选择州: {state_name}")
                time.sleep(0.5)
            except Exception as e:
                print(f"选择州失败: {e}")

            # 输入邮编
            try:
                zip_code = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="Address_ZipCode"]'))
                )
                zip_code.clear()
                zip_code.send_keys(str(row['zip_code']))
                print(f"✓ 输入邮编: {row['zip_code']}")
                time.sleep(0.5)
            except Exception as e:
                print(f"输入邮编失败: {e}")

            # 输入电话
            try:
                phone = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="PhoneNumber"]'))
                )
                phone.clear()
                phone.send_keys(str(row['电话']))
                print(f"✓ 输入电话: {row['电话']}")
                time.sleep(0.5)
            except Exception as e:
                print(f"输入电话失败: {e}")

            # 输入邮箱
            try:
                email = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="EmailAddress"]'))
                )
                email.clear()
                email.send_keys(str(row['邮箱']))
                print(f"✓ 输入邮箱: {row['邮箱']}")
                time.sleep(0.5)
            except Exception as e:
                print(f"输入邮箱失败: {e}")

            # 点击 Next 按钮
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="btnNext"]'))
                )
                next_button.click()
                print("✓ 点击 Next 按钮")
                time.sleep(2)
            except Exception as e:
                print(f"点击 Next 按钮失败: {e}")

            print(f"第 {index + 1} 行数据填写完成")

            # 点击 Next 按钮
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="btnNext"]'))
                )
                next_button.click()
                print("✓ 点击 Next 按钮")
                time.sleep(2)
            except Exception as e:
                print(f"点击 Next 按钮失败: {e}")

            print(f"第 {index + 1} 行数据填写完成")

            # ========== 第二页表单填写 ==========

            # 点击 HasPurchasedBeef
            try:
                has_purchased_beef = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="HasPurchasedBeef"]'))
                )
                has_purchased_beef.click()
                print("✓ 点击 HasPurchasedBeef")
                time.sleep(0.5)
            except Exception as e:
                print(f"点击 HasPurchasedBeef 失败: {e}")

            # 点击 HasPurchaseEligibleState
            try:
                has_purchase_eligible_state = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="HasPurchaseEligibleState"]'))
                )
                has_purchase_eligible_state.click()
                print("✓ 点击 HasPurchaseEligibleState")
                time.sleep(0.5)
            except Exception as e:
                print(f"点击 HasPurchaseEligibleState 失败: {e}")

            # 点击 WasBeefPurchasedEveryMonth
            try:
                was_beef_purchased_every_month = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="WasBeefPurchasedEveryMonth"]'))
                )
                was_beef_purchased_every_month.click()
                print("✓ 点击 WasBeefPurchasedEveryMonth")
                time.sleep(0.5)
            except Exception as e:
                print(f"点击 WasBeefPurchasedEveryMonth 失败: {e}")

            # 输入 EstimatedBeefPurchasedEveryMonth (随机整数 20-40)
            try:
                import random
                estimated_beef = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="EstimatedBeefPurchasedEveryMonth"]'))
                )
                estimated_beef.clear()
                beef_value = random.randint(20, 40)
                estimated_beef.send_keys(str(beef_value))
                print(f"✓ 输入 EstimatedBeefPurchasedEveryMonth: {beef_value}")
                time.sleep(0.5)
            except Exception as e:
                print(f"输入 EstimatedBeefPurchasedEveryMonth 失败: {e}")

            # 输入 EstimateMonthlySpent (随机整数 100-300)
            try:
                import random
                monthly_spent = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="EstimateMonthlySpent"]'))
                )
                monthly_spent.clear()
                spent_value = random.randint(100, 300)
                monthly_spent.send_keys(str(spent_value))
                print(f"✓ 输入 EstimateMonthlySpent: {spent_value}")
                time.sleep(0.5)
            except Exception as e:
                print(f"输入 EstimateMonthlySpent 失败: {e}")

            # 点击 Next 按钮
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="btnNext"]'))
                )
                next_button.click()
                print("✓ 点击 Next 按钮")
                time.sleep(2)
            except Exception as e:
                print(f"点击 Next 按钮失败: {e}")

            # ========== 第三页表单填写 ==========


            time.sleep(20)

            # 点击支付选项按钮
            try:
                payment_option = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="payment"]/div/div/fieldset/div/div/div[2]/div/div[3]/button/span[1]'))
                )
                payment_option.click()
                print("✓ 点击支付选项按钮")
                time.sleep(1)
            except Exception as e:
                print(f"点击支付选项按钮失败: {e}")

            # 点击确认按钮
            try:
                confirm_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[2]/div/div[3]/button[1]/span[1]'))
                )
                confirm_button.click()
                print("✓ 点击确认按钮")
                time.sleep(1)
            except Exception as e:
                print(f"点击确认按钮失败: {e}")

            # 输入手机号
            try:
                phone_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[2]/div/div/div[3]/div/div[2]/div/div/div/input'))
                )
                phone_input.clear()
                phone_input.send_keys("7133848476")
                print("✓ 输入手机号: 7133848476")
                time.sleep(0.5)
            except Exception as e:
                print(f"输入手机号失败: {e}")

            # 点击提交按钮
            try:
                submit_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[2]/div/div/div[4]/button/span[1]'))
                )
                submit_button.click()
                print("✓ 点击提交按钮")
                time.sleep(2)
            except Exception as e:
                print(f"点击提交按钮失败: {e}")


                

            time.sleep(100)







    except Exception as err:
        print(f"Selenium操作出错: {err}")
        import traceback
        traceback.print_exc()
    finally:
        # 通过API关闭浏览器
        stop_data = {"id": browser_id}
        try:
            stop_response = requests.post(
                f"{BASE_URL}/api/stopBrowser",
                headers=headers,
                data=json.dumps(stop_data)
            )
            stop_response_data = stop_response.json()
            print("关闭浏览器响应:", stop_response_data)
        except Exception as err:
            print(f"关闭浏览器时出错: {err}")

        manager.close_browser()


if __name__ == "__main__":
    main()
