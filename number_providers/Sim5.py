import requests 
import traceback
import json

with open(r'number_providers\provider_url_key.json') as f:
    providers = json.loads(f.read())

class Number5Sim():
    def __init__(self, proxyip:str=None, proxyport:int=None, proxyuser:str=None, proxypassword:str=None):
        token = ''
        self.__fixed_url = providers['5sim']['api_url']
        self.__number_details = None
        self.__headers = {
            'Authorization': 'Bearer ' + providers['5sim']['api_key'],
            'Accept': 'application/json',
        }
        if not proxyip:
            self.__proxies = {}
        elif not proxyuser and proxypassword:
            self.__proxies = {
                'http': f'http://{proxyip}:{proxyport}',
                'https': f'http://{proxyip}:{proxyport}'
            }
            
        else:
            self.__proxies = {
                'http': f'http://{proxyuser}:{proxypassword}@{proxyip}:{proxyport}',
                'https': f'http://{proxyuser}:{proxypassword}@{proxyip}:{proxyport}'
            }
            
        self.__available_balance = 0
        self.__rating = 0
        self.phone_number = ""
        self.sms_received = False
        self.otp = ""
        bal = self.get_balance()
        self.min_bal_required = 20
        print(bal)
			
    def get_balance(self):
        try:
            url = f'{self.__fixed_url}/user/profile'
            response = requests.get(url, proxies=self.__proxies, headers=self.__headers)
            if response.status_code == 200:
                data = response.json()
                self.__available_balance = data['balance']
                self.__rating = data['rating']

                return self.__available_balance
            else:
                print(f"error response {response.status_code}")
                return f"error response {response.status_code}"
            
        except Exception as e:
            traceback.print_exc()
            print(e)
            raise Exception("error= {e}")


    def get_product_by_country(self, country='usa', product='yahoo'):
        try:
            url = f'{self.__fixed_url}/guest/prices?country={country}&product={product}'
            response = requests.get(url, proxies=self.__proxies, headers=self.__headers)
            if response.status_code == 200:
                data = dict(response.json())
                return {"status": "success", "data": data}
            else:
                return {'status': 'failed', 'error': response.status_code}

        except Exception as e:
            traceback.print_exc()
            print(e)

    def get_number(self, country='usa', operator='any', product='yahoo'):
        try:
            '''this method only for activation numbers.'''
            url = f'{self.__fixed_url}/user/buy/activation/{country.lower()}/{operator.lower()}/{product.lower()}'
            print(url)
            print(self.__headers)
            response = requests.get(url, proxies=self.__proxies, headers=self.__headers)
            if response.status_code == 200:
                print(response.text)
                data = dict(response.json())
                print(data)
                phone_number = data.pop('phone')
                self.phone_number = phone_number
                self.__number_details = {phone_number: data}
                return {"status": "success", "phone_number": phone_number}
            else:
                return {'status': 'failed', 'error': response.text}
     
        except Exception as e:
            traceback.print_exc()
            return {'status': 'failed', 'error': e}

    def get_sms(self):
        try:
            number_details = self.__number_details.get(self.phone_number)
            id = number_details.get('id', None)
            if id:
                url = f'{self.__fixed_url}/user/check/{id}'
                response = requests.get(url, proxies=self.__proxies, headers=self.__headers)
                if response.status_code == 200:
                    data = dict(response.json())
                    sms = data['sms']
                    if sms:
                        code = sms[0]['code']
                        return {"status": "success", "code": code}
                    else:
                        return {"status": "success", "code": None}
                else:
                    return {'status': 'failed', 'error': response.text}
            else:
                return {'status': 'failed', 'error': 'Invalid phone number id not found in db'}
            
        except Exception as e:
            traceback.print_exc()
            return {'status': 'failed', 'error': e}

    def finish_order(self):
        try:
            number_details = self.__number_details.get(self.phone_number)
            id = number_details.get('id', None)
            if id:
                url = f'{self.__fixed_url}/user/finish/{id}'
                response = requests.get(url, proxies=self.__proxies, headers=self.__headers)
                if response.status_code == 200:
                    data = dict(response.json())
                    if data['status'] == 'FINISHED':
                        return {'status':'success', 'msg': 'Order finished successfully.'}
                    else:
                        return {'status': 'failed', 'error': data['status']}
                else:
                    return {'status': 'failed', 'error': response.text}
            else:
                return {'status': 'failed', 'error': 'Invalid phone number id not found in db'}
        except Exception as e:
            traceback.print_exc()
            return {'status': 'failed', 'error': e}

    def cancel_order(self):
        try:
            number_details = self.__number_details.get(self.phone_number)
            id = number_details.get('id', None)
            if id:
                url = f'{self.__fixed_url}/user/cancel/{id}'
                response = requests.get(url, proxies=self.__proxies, headers=self.__headers)
                if response.status_code == 200:
                    data = dict(response.json())
                    if data['status'] == 'CANCELED':
                        return {'status':'success', 'msg': 'Order cancelled successfully.'}
                    else:
                        return {'status': 'failed', 'error': data['status']}
                else:
                    return {'status': 'failed', 'error': response.text}
            else:
                return {'status': 'failed', 'error': 'Invalid phone number id not found in db'}
        except Exception as e:
            traceback.print_exc()
            return {'status': 'failed', 'error': e}

    def get_countries_list(self):
        try:
            url = f'{self.__fixed_url}/guest/countries'
            response = requests.get(url, proxies=self.__proxies, headers=self.__headers)
            if response.status_code == 200:
                data = dict(response.json())
                print(data)
        except Exception as e:
            traceback.print_exc()

    def __str__(self):
        if all((self.__available_balance, self.__rating)):
            return str('true')
        else:
            return f'available_balance: {self.__available_balance}, rating: {self.__rating}'

            
####### do not uncomment for below code ###############################################
# from Sim5 import Number5Sim
# Number5Sim_obj = Number5Sim()
# print(Number5Sim_obj)
# number = Number5Sim_obj.get_number(country='india', operator='any', product='yahoo')
# print(number)
# status = Number5Sim_obj.cancel_order()
# print(status)

#######################################################################################
	