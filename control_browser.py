import inspect
import sys
from playwright.sync_api import sync_playwright, TimeoutError
# from playwright._impl._api_types import TimeoutError, Error
import traceback
import random


class ControlBrowsers:
    def __init__(self, proxy_ip, proxy_port, proxy_user=None, proxy_password=None):
        print("class ControlBrowsers")
        self.proxy_ip = proxy_ip
        self.proxy_port = proxy_port
        self.proxy_user = proxy_user
        self.proxy_password = proxy_password
        self.playwright,  self.pw_browser, self.pw_context, self.page = None, None, None, None
        self.browserReady = False
        if self.proxy_ip == '1.1.1.1':
            self.browser_proxy = {}
        elif self.proxy_user in ('NA', None, '', False) or self.proxy_password in ('NA', None, '', False):
            self.browser_proxy = {"server": f"http://{self.proxy_ip}:{self.proxy_port}"}
        else:
            self.browser_proxy = {
                "server": f"http://{self.proxy_ip}:{self.proxy_port}",
                "username": self.proxy_user,
                "password": self.proxy_password
            }

        self.openBrowser()

    def __get_random_user_agent(self):
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.198 Safari/537.36",
            # Add more User-Agent strings
        ]
        return random.choice(user_agents)

    def __getBrowser(self, browser_name="chrome", headless=False):
        try:
            playwright = sync_playwright().start()

            if self.browser_proxy:
                print(f"browser_proxy: {self.browser_proxy}")
                browser = playwright.chromium.launch(channel=browser_name, headless=headless, proxy=self.browser_proxy)
            else:
                browser = playwright.chromium.launch(channel=browser_name, headless=headless, proxy=None)
           
            user_context = browser.new_context(viewport={'width': 1600, 'height': 900},
                                               user_agent=self.__get_random_user_agent(),
                                               java_script_enabled=True)

            return playwright, browser, user_context
        except Exception as e:
            traceback.print_exc()
            # print(f"{inspect.stack()[1][3]}_{sys.exc_info()[2].tb_lineno};{e}")
            raise Exception(f"{inspect.stack()[1][3]}_{sys.exc_info()[2].tb_lineno};{e}")

    def openBrowser(self):
        try:
            print("opening Browser...")
            playwright, pw_browser, pw_context = self.__getBrowser()
            self.playwright = playwright
            self.pw_browser = pw_browser
            self.pw_context = pw_context
            self.pw_context.grant_permissions(["clipboard-read", "clipboard-write"])

            if self.pw_context:
                self.b = self.pw_context
            else:
                self.b = self.pw_browser
            self.page = self.b.new_page()
            # self.page.set_default_navigation_timeout(20000)

        except Exception as e:
            raise Exception("could not open browser")

        try:
            self.page.goto("https://google.com", wait_until="networkidle",timeout=50000)
        except TimeoutError as e:
            print("could not open google.com in 50 seconds; {e}")
            raise Exception("could not open google.com in 50 seconds")
        # except Error as e:
        #     if "ERR_TIMED_OUT" in str(e):
        #         raise Exception("ERR_TIMED_OUT")
        #     else:
        #         raise Exception("proxy issue")
        self.browserReady = True
        return True

    def wait(self, timeout=1):
        self.page.wait_for_timeout(1000*timeout)

    # def wait_until_page_load()

    def wait_for_element(self, search_for="", element_name="<not_given>", critical=True, timeout=0.5, state="visible"):
        try:
            self.page.set_default_timeout(timeout * 1000)
            # print(self.page.query_selector_all(search_for))
            if self.page.wait_for_selector(search_for, timeout=timeout*1000, state=state):
                return True
            elif critical:
                raise Exception(f"could not find element: {element_name}")
            else:
                return False
        except TimeoutError:
            if critical:
                raise Exception(f"could not find element: {element_name}")
            else:
                return False
        except Exception as e:
            raise Exception(f"{inspect.stack()[1][3]}_{sys.exc_info()[2].tb_lineno};{e}")
        

    def click(self, search_for="", element_name="<not_given>", critical=True, timeout=5, state="visible"):
        try:
            self.page.set_default_timeout(timeout * 1000)
            # self.page.click(search_for)
            self.page.wait_for_selector(search_for, state=state).click()
            return True
        except TimeoutError:
            if critical:
                raise Exception(f"could not click on {element_name}")
            else:
                return False
        except Exception as e:
            raise Exception(f"{inspect.stack()[1][3]}_{sys.exc_info()[2].tb_lineno};{e}")


    def search(self, search_for="", element_name="<not_given>", ele=None, critical=True, timeout=2):
        try:
            self.page.set_default_timeout(timeout * 1000)
            if ele:
                eles = ele.locator(search_for)
            else:
                eles = self.page.locator(search_for)

            if eles.count() > 0:
                return eles
            elif critical:
                raise Exception(f"could not search for {element_name}.")
            else:
                return False
        except TimeoutError as e:
            print(e)
            if critical:
                traceback.print_exc()
                raise Exception(f"could not search for {element_name}")
            else:
                return False
        except Exception as e:
            raise Exception(f"{inspect.stack()[1][3]}_{sys.exc_info()[2].tb_lineno};{e}")

    def current_url(self):
        try:
            current_url = None
            current_url = self.page.url
            return current_url
        except Exception as e:
            raise Exception(f"{inspect.stack()[0][3]}_{sys.exc_info()[2].tb_lineno};{e}")

    def type(self, search_for="", fill="", element_name="<not_given>", critical=True, timeout=20, speed=100,
             state="visible"):
        try:
            self.page.set_default_timeout(timeout * 1000)
            # self.page.type(search_for, fill, delay=speed)
            self.page.wait_for_selector(search_for, state=state).type(fill, delay=speed)

        except TimeoutError:
            if critical:
                raise Exception(f"could not search/type in {element_name}")
            else:
                return False
        except Exception as e:
            raise Exception(f"{inspect.stack()[1][3]}_{sys.exc_info()[2].tb_lineno};{e}")


    def goto(self, url, timeout=30, wait_for="load"):
        # wait_for="domcontentloaded"
        # wait_for="networkidle"
        try:
            if timeout > 170:
                timeout = 170

            self.page.set_default_navigation_timeout(timeout * 1000)
            self.page.goto(url, wait_until=wait_for)
            return True

        # self.page.close()
        # self.pw_context.new_page()
        # self.page = self.pw_context.pages[-1]
        except TimeoutError:
            return False
        except Exception as e:
            raise Exception(f"{inspect.stack()[1][3]}_{sys.exc_info()[2].tb_lineno};{e}")


    def quit_browser(self):
        try:
            self.page.close()
            self.pw_context.close()
            self.pw_browser.close()
            self.playwright.stop()
        except Exception as e:
            print(e)

    def closeOtherTabs(self):
        try:
            close_idx = 0
            while close_idx != -1:
                close_idx = -1
                for idx, page in enumerate(self.pw_context.pages):
                    if page != self.page:
                        close_idx = idx
                        break
                if close_idx > -1:
                    self.pw_context.pages[close_idx].close()
        except:
            print(f'closeOtherTabs error :: {sys.exc_info()[0]}')
  

# if __name__ =="__main__":
#     proxyip = '88.218.175.133'
#     proxyport = 29842
#     proxyuser = 'rmoron'
#     proxypassword = 'DHx1K3mr'
#     b = ControlBrowsers(proxyip, proxyport, proxyuser, proxypassword)
#     b.openBrowser()
#     b.page.wait_for_timeout(10000)
