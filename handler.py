from control_browser import ControlBrowsers
from faker import Faker
import gender_guesser.detector as gender
import requests
import string
import secrets
import random
from datetime import datetime, timedelta
import traceback
import sqlite3
from global_var import iso_countries
from number_providers.Sim5 import Number5Sim
from number_providers.sms_activation_service import SmsActivationService
import time


db_con = sqlite3.connect("emails.db")
db_cur = db_con.cursor()

# Create a table
db_cur.execute('''
CREATE TABLE IF NOT EXISTS email_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    dob TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    country TEXT,
    status INTEGER DEFAULT 1,
    cookies TEXT
)
''')
db_con.commit()
db_con.close()

def generate_birth_date():
    today = datetime.today()

    # Generate a random number of days (at least 18 years ago)
    days_in_18_years = 18 * 365  # Approximate number of days in 18 years

    # Randomly pick a date older than 18 years
    random_days = random.randint(days_in_18_years, 55 * 365)  # Random date between 18 years and 55 years ago
    random_date = today - timedelta(days=random_days)
    year, month, day = random_date.strftime('%Y-%B-%d').split('-')
    return year, month, day

def generate_password(length=12):
    # Define the characters to choose from
    characters = string.ascii_letters + string.digits + '@.@..@@'
    
    # Generate a random password of the specified length
    password = ''.join(secrets.choice(characters) for _ in range(length))
    
    return password

def get_ip_loc(proxy=None):
    try:
        if "username" in proxy and "password" in proxy:
            proxies = {'http': f'{proxy["username"]}:{proxy["password"]}@{proxy["server"]}', 
                       'https': f'{proxy["username"]}:{proxy["password"]}@{proxy["server"]}'}
        elif "server" in proxy:
            proxies = {'http': f'{proxy["server"]}',
                       'https': f'{proxy["server"]}'}
        else:
            proxies = {}
        url = 'http://ipinfo.io/json' 
        response = requests.get(url, proxies=proxies) 
        data = response.json() 
        city = data['city'] 
        country = data['country'] 
        region = data['region']
        print(city, region, country)
        return iso_countries[country]
    except Exception as e:
        traceback.print_exc()




class Handler(ControlBrowsers):
    def __init__(self, proxy_ip, proxy_port, proxy_user=None, proxy_password=None, number_provider='5sim'):
        if number_provider[0] not in ('5sim', 'sms_activation_service', 'smspva'):
            raise Exception('logic not implemented for provider: ' + str(number_provider[0]))
        super().__init__(proxy_ip, proxy_port, proxy_user, proxy_password)
        fake = Faker()
        d = gender.Detector()
        self.first_name = fake.first_name()
        self.last_name = fake.last_name()
        email_ = [self.first_name, self.last_name]
        random.shuffle(email_)
        print(email_)
        self.email = ''.join(email_)+str(random.randint(100,9999))
        self.gender = d.get_gender(self.first_name)
        self.password = generate_password(random.choice(range(10, 16)))
        self.year, self.month, self.day = generate_birth_date()
        self.country = '' # get_ip_loc(self.browser_proxy)
        self.account_created = False
        self.number_order_status = False
        print(f'number provider: {number_provider[0]}')
        if number_provider[0] == '5sim':
            self.number_provider = Number5Sim(number_provider[1], number_provider[2])
            if float(self.number_provider.get_balance()) < self.number_provider.min_bal_required:
                cur = db_con.cursor()

                raise Exception(f'balance is too low please top up your number provider: {number_provider}, current balance: {self.number_provider.get_balance()}')

        elif number_provider == 'sms-activation-service':
            self.number_provider = SmsActivationService(number_provider[1], number_provider[2])
            if float(self.number_provider.get_balance()) < self.number_provider.min_bal_required:
                raise Exception(f'balance is too low please top up your number provider: {number_provider}, current balance: {self.number_provider.get_balance()}')
        elif number_provider == 'smspva':
            pass
            # self.number_provider = 'smspva'

        print(f''''email: {self.email}\nfirst name: {self.first_name}\nlast name: {self.last_name}\ngender: {self.gender}\n password: {self.password}\nyear: 
              {self.year}\nmonth: {self.month}\nday: {self.day}\ncountry: {self.country}\n''')
        
    def captcha_varification(self):
        try:
            if self.search(search_for='[id="recaptcha-iframe"]:visible', element_name='check for recaptcha', timeout=2, critical=False):
                api_key = 'c7bca2a6efa7e6b32ba423bdb8cd45ee'
                frame = self.page.frame_locator('[id="recaptcha-iframe"]:visible')
                src = frame.locator('[title="reCAPTCHA"]:visible').get_attribute("src")
                page_url = src
                site_key = frame.locator('div[data-sitekey]').get_attribute("data-sitekey")
                frame.locator('[id="g-recaptcha-response"]').count()

                form = {"method": "userrecaptcha",
                        "googlekey": site_key,
                        "key": api_key,
                        "pageurl": page_url,
                        "json": 1}
                print(form)

                
                response = requests.post('http://2captcha.com/in.php', data=form)

                response.status_code == 200
                request_id = response.json()['request']

                url = f"http://2captcha.com/res.php?key={api_key}&action=get&id={request_id}&json=1"

                js2 = """parent.postMessage({
                                recaptchaResponse: grecaptcha.enterprise.getResponse(recaptchaWidget),
                                acrumb: recaptchaForm.acrumb.value,
                                crumb: recaptchaForm.crumb.value,
                                sessionIndex: recaptchaForm.sessionIndex.value,
                                context: recaptchaForm.context.value
                            }, 'https://login.yahoo.com');"""

                status = 0
                st = int(time.time())
                while not status and int(time.time()) < st + 150:
                    res = requests.get(url)
                    print(res.json())
                    if res.json()['status'] == 0:
                        time.sleep(3)
                    else:
                        requ = res.json()['request']
                        js = f'document.getElementById("g-recaptcha-response").innerHTML="{requ}";'
                        self.page.set_default_timeout(3*1000)
                        frame.locator('[id="g-recaptcha-response"]').evaluate(js)
                        frame.locator('//html').evaluate(js2)

                        # js = f'document.getElementById("recaptcha-submit").removeAttribute("disabled");'
                        # frame.locator('[id="recaptcha-submit"]').evaluate(js)
                        # frame.locator('[id="recaptcha-submit"]').click()
                        # print('solved')
                        break
                return True
            else:
                return False
        except Exception as e:
            traceback.print_exc()


    def run(self):
        try:
            # self.goto('https://mail.yahoo.com', timeout=150000)
            # self.click(search_for='//a[contains(text(), "Sign in")]', element_name='sign in button', critical=False)
            # self.page.wait_for_load_state(state="load", timeout=150000)
            self.page.goto('https://login.yahoo.com/?.src=ym&lang=en-US', timeout=500000)
            self.wait(2)
            if not self.click(search_for='//a[@id="createacc"]', element_name='create account button', timeout=10, critical=False):
                self.click(search_for='//a[@id="createacc"]', element_name='create account button2', timeout=10)
            self.wait(5)
            self.page.wait_for_load_state(state="networkidle", timeout=240000)
            self.wait(2)
            self.click(search_for='//div[@id="usernamereg-fullname"]', element_name='click full name')
            self.wait()
            self.click(search_for='//input[@id="usernamereg-firstName"]', element_name='first name')
            self.page.keyboard.type(self.first_name, delay=random.choice(range(40, 200)))
            self.click(search_for='//input[@id="usernamereg-lastName"]', element_name='last name')
            self.page.keyboard.type(self.last_name, delay=random.choice(range(40, 200)))
            self.click(search_for='//input[@id="usernamereg-userId"]', element_name='enater userid')
            self.page.keyboard.type(self.email, delay=random.choice(range(40, 200)))
            self.click(search_for='//input[@id="usernamereg-password"]', element_name='enter password')
            self.page.keyboard.type(self.password, delay=random.choice(range(40, 200)))
            self.wait()
            self.page.select_option('//select[@id="usernamereg-month"]', self.month)
            self.click(search_for='//input[@id="usernamereg-day"]', element_name='click day')
            self.page.keyboard.type(self.day, delay=random.choice(range(40, 200)))
            self.click(search_for='//input[@id="usernamereg-year"]', element_name='click year')
            self.page.keyboard.type(self.year, delay=random.choice(range(40, 200)))
            self.wait(2)
            
            self.click(search_for='//button[@id="reg-submit-button"]', element_name='submit button')
            self.page.wait_for_load_state(state="load", timeout=240000)

            if self.search(search_for='//div[@id="reg-error-userId"]', element_name='error message', critical=False, timeout=5):
                self.email += f'{random.randint(0,9)}'
                print(self.email)
                self.click(search_for='//input[@id="usernamereg-userId"]', element_name='enater userid')
                self.page.keyboard.press('Control+A')
                self.page.keyboard.press('Backspace')
                self.page.keyboard.type(self.email, delay=random.choice(range(40, 200)))
                self.click(search_for='//button[@id="reg-submit-button"]', element_name='submit button')
            self.wait(5)
            self.page.wait_for_load_state(state="load", timeout=240000)
            if not self.search(search_for='//h2[contains(text(), "Add your phone")]', element_name='add phone button', timeout=10):
                self.quit_browser()
                return False
            try:
                iso = self.page.locator('//select[@name="shortCountryCode"]/option').get_attribute('value', timeout=2000)
                self.country = iso_countries[iso]
                print(f'ditected country by yahoo: {self.country}')
            except:
                print('did not get country')
            cnt = 10
            while cnt:
                cnt-=1
                number_status = self.number_provider.get_number(country=self.country)
                if number_status['status'] != 'success':
                    print(number_status)
                    self.quit_browser()
                    return False
                self.number_order_status = True
                print(number_status)
                self.wait(2)
                self.click(search_for='//input[@id="usernamereg-phone"]', element_name='enter phone number')
                self.page.keyboard.press('Control+A')
                self.page.keyboard.press('Backspace')
                self.page.keyboard.type(number_status['phone_number'], delay=random.choice(range(40, 200)))
                self.wait(5)
                self.page.wait_for_load_state(state="networkidle", timeout=240000)
                if not self.click(search_for='//button[@id="reg-sms-button"]', element_name='send sms button', timeout=20, critical=False):
                    self.click(search_for='//button[contains(text(),"Get code by")]', element_name='get code by button', timeout=20)
                self.page.wait_for_load_state(state="networkidle", timeout=240000)
                self.wait(5)
                if self.search(search_for='//div[contains(text(), "There are already accounts associated with this phone number")]', 
                            element_name='phone number already in use', timeout=10, critical=False):
                    print('account already exist for: ', number_status['phone_number'])
                    print('getting new number after 2 minutes.')
                    self.wait(130)
                    self.number_provider.cancel_order()
                    self.number_order_status = False
                    continue
                if self.search(search_for='//div[@id="reg-error-phone"]', element_name='check error phone', critical=False):
                    print('getting new number after 2 minutes.')
                    self.wait(130)
                    self.number_provider.cancel_order()
                    self.number_order_status = False
                    continue
                self.page.wait_for_load_state(state="networkidle", timeout=240000)
                if self.captcha_varification():
                    self.wait(2)
                    self.page.wait_for_load_state(state="networkidle", timeout=240000)
                self.wait(2)
                if self.search(search_for='//h2[contains(text(), "Too many failed")]', element_name='too many failed', timeout=10, critical=False):
                    return 'too many failed attempt'
                if self.search(search_for='//div[@id="phone-verify-challenge"]', element_name='verify otp', timeout=5, critical=False):
                    break


            self.wait(15)
            cnt = 40
            while cnt:
                self.wait(5)
                cnt -= 1
                
                sms_status = self.number_provider.get_sms()
                if sms_status['status'] == 'success':
                    if sms_status['code']:
                        self.click(search_for='//input[@id="verification-code-field"]', element_name='enter otp')
                        self.page.keyboard.press('Control+A')
                        self.wait(0.5)
                        self.page.keyboard.press('Backspace')
                        self.wait(0.5)
                        self.page.keyboard.type(sms_status['code'], delay=random.choice(range(40, 200)))
                        self.wait(2)
                        self.click(search_for='//button[@id="verify-code-button"]', element_name='verify otp button', timeout=20)

                        self.wait(5)
                        self.page.wait_for_load_state(state="load", timeout=240000)
                        if self.search(search_for='//div[@data-error="messages.VERIFICATION_FAILED"]', element_name='error code', timeout=5, critical=False):
                            continue
                        if self.search(search_for='//p[contains(text(), "Welcome to Yahoo!")]', element_name='success', critical=False):
                            self.click(search_for='//button[contains(text(), "Done")]', element_name='done', critical=False)
                            self.click(search_for='//button[@aria-label="Close"]', element_name='close pop-up', critical=False)
                            self.account_created = True
                            break
                    else:
                        print('waiting for otp....')
                        continue
            else:
                self.number_provider.cancel_order()
                self.number_order_status = False
                self.quit_browser()
                raise Exception('Failed to get SMS code')
            self.wait(2)

            if self.account_created:
                user_data = (
                        self.email,  # email
                        self.password,       # password (hashed, not plain text)
                        self.first_name,                  # first_name
                        self.last_name,                   # last_name
                        self.country,                   # country
                        '{}'  # cookies (as JSON string or plain text)
                    )

                print(user_data)
                # Insert the data
                db_cur = db_con.cursor()
                db_cur.execute('''
                INSERT INTO users (email, password, first_name, last_name, country, cookies)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', user_data)

                # Commit changes
                db_con.commit()
                db_con.close()
                self.number_provider.finish_order()

            self.wait(10)
            self.quit_browser()

        except Exception as e:
            traceback.print_exc()
            print('waiting for cancel number..')
            cnt = 30
            if self.number_order_status:
                while cnt:
                    print('waiting for cancel number..')
                    status = self.number_provider.cancel_order()
                    self.number_order_status = False
                    if status['status'] == 'success':
                        break
                    time.sleep(5)




if __name__ == "__main__":
    # obj = Handler('proxy.okeyproxy.com', 31212, proxy_user='customer-jrs3267456-country-IN', proxy_password='de7cakrz', number_provider='sms-activation-service')
    obj = Handler('proxy.okeyproxy.com', 31212, proxy_user='customer-jrs3267456-country-IN', proxy_password='de7cakrz', number_provider='5sim')
    # obj = Handler('1.1.1.1', 12233, number_provider='sms-activation-service')
    obj.run()

