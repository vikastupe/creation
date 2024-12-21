import requests 
import traceback
import json

with open(r'number_providers\provider_url_key.json') as f:
    providers = json.loads(f.read())

class SmsActivationService():
    def __init__(self, proxyip:str=None, proxyport:int=None, proxyuser:str=None, proxypassword:str=None):
        token = ''
        self.__fixed_url = providers['sms_activation_service']['api_url']+f"/stubs/handler_api?api_key={providers['sms_activation_service']['api_key']}&lang=en&"
        self.__number_details = None
        self.__headers = {}
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
        self.min_bal_required = 0.1
        print(bal)
			
    def get_balance(self):
        try:
            url = f'{self.__fixed_url}action=getBalance'
            response = requests.get(url, proxies=self.__proxies, headers=self.__headers)
            if response.status_code == 200:
                data = response.text
                self.__available_balance = data
                return self.__available_balance
            else:
                print(f"error response {response.status_code}")
                return f"error response {response.status_code}"
            
        except Exception as e:
            traceback.print_exc()
            print(e)
            raise Exception("error= {e}")


    def get_number(self, country='usa', operator='any', product='yahoo'):
        try:
            '''this method only for activation numbers.'''
            print(f'SmsActivationService: get number called')
            for i in country_operator:
                if i['name'].lower() == country.lower():
                    country_id = i['id']
            else:
                for i in country_operator:
                    if i['name'].lower() == country.split()[0].lower():
                        country_id = i['id']
                        break
                else:
                    return {'status': 'failed', 'error': 'country not found'}
            
            product = 'mb' # this is for yahoo only
            url = f'{self.__fixed_url}action=getNumber&service={product}&operator={operator}&country={country_id}'
            response = requests.get(url, proxies=self.__proxies, headers=self.__headers)
            if response.status_code == 200:
                data = response.text
                print(data)
                if 'ACCESS_NUMBER' in data:
                    id = data.split(':')[1]
                    self.phone_number = data.split(':')[2][2:]
                    self.__number_details = {self.phone_number: {'id': id}}
                    return {"status": "success", "phone_number": self.phone_number}
                else:
                    print(data)
                    return {'status': 'failed', 'error': data}
            else:
                print(response.text)
                return {'status': 'failed', 'error': response.text}
    
        except Exception as e:
            traceback.print_exc()
            return {'status': 'failed', 'error': e}

    def get_sms(self):
        try:
            number_details = self.__number_details.get(self.phone_number)
            id = number_details.get('id', None)
            if id:
                url = f'{self.__fixed_url}action=getStatus&id={id}'
                response = requests.get(url, proxies=self.__proxies, headers=self.__headers)
                if response.status_code == 200:
                    data = response.text
                    print(data)
                    if 'STATUS_OK' in data:
                        return {"status": "success", "code": data.split(':')[1]}
                    elif 'STATUS_WAIT_CODE' in data:
                        return {"status": "success", "code": None}
                    else:
                        
                        return {'status': 'failed', 'error': data}
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
                url = f'{self.__fixed_url}action=setStatus&id={id}&status=6'
                response = requests.get(url, proxies=self.__proxies, headers=self.__headers)
                if response.status_code == 200:
                    data = response.text
                    if 'ACCESS_ACTIVATION' in data:
                        return {'status':'success', 'msg': 'Order finished successfully.'}
                    else:
                        return {'status': 'failed', 'error': data}
                else:
                    return {'status': 'failed', 'error': response.text}
            else:
                return {'status': 'failed', 'error': 'Invalid phone number id not found in db'}
        except Exception as e:
            traceback.print_exc()
            return {'status': 'failed', 'error': e}

    def cancel_order(self):
        '''Order cancel only after 2 minutes of order creation'''
        try:
            number_details = self.__number_details.get(self.phone_number)
            id = number_details.get('id', None)
            if id:
                url = f'{self.__fixed_url}action=setStatus&id={id}&status=8'
                response = requests.get(url, proxies=self.__proxies, headers=self.__headers)
                if response.status_code == 200:
                    data = response.text
                    if 'ACCESS_CANCEL' == data:
                        return {'status':'success', 'msg': 'Order cancelled successfully.'}
                    else:
                        return {'status': 'failed', 'error': data}
                else:
                    return {'status': 'failed', 'error': response.text}
            else:
                return {'status': 'failed', 'error': 'Invalid phone number id not found in db'}
            
        except AttributeError:
            raise AttributeError('Phone number not found in db')
        except Exception as e:
            traceback.print_exc()
            return {'status': 'failed', 'error': e}

    # def get_countries_list(self):
    #     try:
    #         url = f'{self.__fixed_url}action=getCountryAndOperators'
    #         response = requests.get(url, proxies=self.__proxies, headers=self.__headers)
    #         if response.status_code == 200:
    #             data = dict(response.json())
    #             print(data)
    #     except Exception as e:
    #         traceback.print_exc()

    def __str__(self):
        if self.__available_balance:
            return str('true')
        else:
            return f'available_balance: {self.__available_balance}'


country_operator = [
  {
    "id": 0,
    "name": "Russia",
    "operators": {
      "any": "any",
      "aiva": "aiva",
      "beeline": "beeline",
      "center2m": "center2m",
      "danycom": "danycom",
      "ezmobile": "ezmobile",
      "gazprombank_mobile": "gazprombank_mobile",
      "lycamobile": "lycamobile",
      "matrix": "matrix",
      "mcn": "mcn",
      "megafon": "megafon",
      "motiv": "motiv",
      "mts": "mts",
      "mtt": "mtt",
      "mtt_virtual": "mtt_virtual",
      "patriot": "patriot",
      "rostelecom": "rostelecom",
      "sber": "sber",
      "simsim": "simsim",
      "tele2": "tele2",
      "tinkoff": "tinkoff",
      "ttk": "ttk",
      "vector": "vector",
      "vtb_mobile": "vtb_mobile",
      "winmobile": "winmobile",
      "yota": "yota"
    }
  },
  {
    "id": 1,
    "name": "Ukraine",
    "operators": {
      "any": "any",
      "3mob": "3mob",
      "intertelecom": "intertelecom",
      "kyivstar": "kyivstar",
      "life": "life",
      "lycamobile": "lycamobile",
      "mts": "mts",
      "utel": "utel",
      "vodafone": "vodafone"
    }
  },
  {
    "id": 2,
    "name": "Kazakhstan",
    "operators": {
      "any": "any",
      "activ": "activ",
      "altel": "altel",
      "beeline": "beeline",
      "forte mobile": "forte mobile",
      "kcell": "kcell",
      "tele2": "tele2"
    }
  },
  {
    "id": 3,
    "name": "China",
    "operators": {
      "any": "any",
      "china_unicom": "china_unicom",
      "chinamobile": "chinamobile",
      "unicom": "unicom"
    }
  },
  {
    "id": 4,
    "name": "Philippines",
    "operators": {
      "any": "any",
      "globe telecom": "globe telecom",
      "smart": "smart",
      "sun cellular": "sun cellular",
      "tm": "tm"
    }
  },
  {
    "id": 5,
    "name": "Myanmar",
    "operators": {
      "any": "any",
      "mpt": "mpt",
      "mytel": "mytel",
      "ooredoo": "ooredoo",
      "telenor": "telenor"
    }
  },
  {
    "id": 6,
    "name": "Indonesia",
    "operators": {
      "any": "any",
      "axis": "axis",
      "indosat": "indosat",
      "smartfren": "smartfren",
      "telkomsel": "telkomsel",
      "three": "three"
    }
  },
  {
    "id": 7,
    "name": "Malaysia",
    "operators": {
      "any": "any",
      "celcom": "celcom",
      "digi": "digi",
      "electcoms": "electcoms",
      "hotlink": "hotlink",
      "indosat": "indosat",
      "maxis": "maxis",
      "telekom": "telekom",
      "tune_talk": "tune_talk",
      "u_mobile": "u_mobile",
      "unifi": "unifi",
      "xox": "xox",
      "yes": "yes",
      "yoodo": "yoodo"
    }
  },
  {
    "id": 8,
    "name": "Kenya",
    "operators": {
      "any": "any",
      "airtel": "airtel",
      "econet": "econet",
      "orange": "orange",
      "safaricom": "safaricom",
      "telkom": "telkom"
    }
  },
  {
    "id": 9,
    "name": "Tanzania",
    "operators": {
      "any": "any",
      "airtel": "airtel",
      "halotel": "halotel",
      "tigo": "tigo",
      "ttcl": "ttcl",
      "vodacom": "vodacom"
    }
  },
  {
    "id": 10,
    "name": "Vietnam",
    "operators": {
      "any": "any",
      "itelecom": "itelecom",
      "mobifone": "mobifone",
      "vietnamobile": "vietnamobile",
      "viettel": "viettel",
      "vinaphone": "vinaphone",
      "wintel": "wintel"
    }
  },
  {
    "id": 11,
    "name": "Kyrgyzstan",
    "operators": {
      "any": "any",
      "beeline": "beeline",
      "megacom": "megacom",
      "nurtel": "nurtel",
      "o!": "o!"
    }
  },
  {
    "id": 12,
    "name": "USA (Virtual)",
    "operators": {
      "any": "any",
      "tmobile": "tmobile"
    }
  },
  {
    "id": 13,
    "name": "Israel",
    "operators": {
      "any": "any",
      "018 xphone": "018 xphone",
      "019mobile": "019mobile",
      "azi": "azi",
      "cellcom": "cellcom",
      "golan telecom": "golan telecom",
      "home_cellular": "home_cellular",
      "hot_mobile": "hot_mobile",
      "jawwal": "jawwal",
      "ooredoo": "ooredoo",
      "orange": "orange",
      "pali": "pali",
      "partner": "partner",
      "pelephone": "pelephone",
      "rami_levy": "rami_levy"
    }
  },
  {
    "id": 14,
    "name": "Hong Kong (China)",
    "operators": {
      "any": "any",
      "chinamobile": "chinamobile",
      "csl_mobile": "csl_mobile",
      "imc": "imc",
      "lucky_sim": "lucky_sim",
      "pccw": "pccw",
      "smartone": "smartone",
      "three": "three",
      "unicom": "unicom"
    }
  },
  {
    "id": 15,
    "name": "Poland",
    "operators": {
      "any": "any",
      "a2_mobile": "a2_mobile",
      "aero2": "aero2",
      "e_telko": "e_telko",
      "heyah": "heyah",
      "klucz": "klucz",
      "lycamobile": "lycamobile",
      "netia": "netia",
      "nju": "nju",
      "orange": "orange",
      "play": "play",
      "plus": "plus",
      "plush": "plush",
      "red_bull_mobile": "red_bull_mobile",
      "tmobile": "tmobile",
      "virgin": "virgin"
    }
  },
  {
    "id": 16,
    "name": "England (UK)",
    "operators": {
      "any": "any",
      "airtel": "airtel",
      "cmlink": "cmlink",
      "ee": "ee",
      "ezmobile": "ezmobile",
      "giffgaff": "giffgaff",
      "lebara": "lebara",
      "lycamobile": "lycamobile",
      "o2": "o2",
      "orange": "orange",
      "talk_telecom": "talk_telecom",
      "tata_communications": "tata_communications",
      "teleena": "teleena",
      "three": "three",
      "tmobile": "tmobile",
      "vectone": "vectone",
      "vodafone": "vodafone"
    }
  },
  {
    "id": 17,
    "name": "Madagascar",
    "operators": {
      "any": "any",
      "orange": "orange"
    }
  },
  {
    "id": 18,
    "name": "Congo",
    "operators": {
      "any": "any",
      "africel": "africel",
      "airtel": "airtel",
      "orange": "orange",
      "vodacom": "vodacom"
    }
  },
  {
    "id": 19,
    "name": "Nigeria",
    "operators": {
      "any": "any",
      "airtel": "airtel",
      "etisalat": "etisalat",
      "glomobile": "glomobile",
      "mtn": "mtn"
    }
  },
  {
    "id": 20,
    "name": "Macau",
    "operators": {
      "any": "any",
      "3macao": "3macao"
    }
  },
  {
    "id": 21,
    "name": "Egypt",
    "operators": {
      "any": "any",
      "etisalat": "etisalat",
      "orange": "orange",
      "vodafone": "vodafone",
      "we": "we"
    }
  },
  {
    "id": 22,
    "name": "India",
    "operators": {
      "any": "any",
      "airtel": "airtel"
    }
  },
  {
    "id": 23,
    "name": "Ireland",
    "operators": {
      "any": "any",
      "48mobile": "48mobile",
      "cablenet": "cablenet",
      "eir": "eir",
      "lycamobile": "lycamobile",
      "tesco": "tesco",
      "vodafone": "vodafone"
    }
  },
  {
    "id": 24,
    "name": "Cambodia",
    "operators": {
      "any": "any",
      "metfone": "metfone",
      "smart": "smart"
    }
  },
  {
    "id": 25,
    "name": "Laos",
    "operators": {
      "any": "any",
      "beeline": "beeline",
      "etl": "etl",
      "laotel": "laotel",
      "telekom": "telekom",
      "tplus": "tplus",
      "unitel": "unitel"
    }
  },
  {
    "id": 26,
    "name": "Haiti",
    "operators": {
      "any": "any",
      "natcom": "natcom"
    }
  },
  {
    "id": 27,
    "name": "Côte d'Ivoire",
    "operators": {
      "any": "any",
      "moov": "moov",
      "mtn": "mtn",
      "orange": "orange"
    }
  },
  {
    "id": 28,
    "name": "Gambia",
    "operators": {
      "any": "any",
      "africel": "africel",
      "comium": "comium",
      "gamcel": "gamcel",
      "qcell": "qcell"
    }
  },
  {
    "id": 29,
    "name": "Serbia",
    "operators": {
      "any": "any",
      "a1": "a1",
      "globaltel": "globaltel",
      "mobtel": "mobtel",
      "mts": "mts",
      "vip": "vip"
    }
  },
  {
    "id": 30,
    "name": "Yemen",
    "operators": {
      "any": "any",
      "mtn": "mtn",
      "sabafon": "sabafon",
      "yemen_mobile": "yemen_mobile"
    }
  },
  {
    "id": 31,
    "name": "South Africa",
    "operators": {
      "any": "any",
      "cell c": "cell c",
      "lycamobile": "lycamobile",
      "mtn": "mtn",
      "neotel": "neotel",
      "telkom": "telkom",
      "vodacom": "vodacom"
    }
  },
  {
    "id": 32,
    "name": "Romania",
    "operators": {
      "any": "any",
      "benefito_mobile": "benefito_mobile",
      "digi": "digi",
      "lycamobile": "lycamobile",
      "my_avon": "my_avon",
      "orange": "orange",
      "runex_telecom": "runex_telecom",
      "telekom": "telekom",
      "vodafone": "vodafone"
    }
  },
  {
    "id": 33,
    "name": "Colombia",
    "operators": {
      "any": "any",
      "claro": "claro",
      "etb": "etb",
      "exito": "exito",
      "links_field": "links_field",
      "movistar": "movistar",
      "tigo": "tigo",
      "virgin": "virgin",
      "wom": "wom"
    }
  },
  {
    "id": 34,
    "name": "Estonia",
    "operators": {
      "any": "any",
      "elisa": "elisa",
      "goodline": "goodline",
      "super": "super",
      "tele2": "tele2",
      "telia": "telia",
      "topconnect": "topconnect"
    }
  },
  {
    "id": 35,
    "name": "Azerbaijan",
    "operators": {
      "any": "any",
      "azercell": "azercell",
      "azerfon": "azerfon",
      "bakcell": "bakcell",
      "humans": "humans",
      "nar mobile": "nar mobile",
      "naxtel": "naxtel"
    }
  },
  {
    "id": 36,
    "name": "Canada (virtual)",
    "operators": {
      "any": "any",
      "cellular": "cellular",
      "chatrmobile": "chatrmobile",
      "fido": "fido",
      "lucky": "lucky",
      "rogers": "rogers",
      "telus": "telus"
    }
  },
  {
    "id": 37,
    "name": "Morocco",
    "operators": {
      "any": "any",
      "iam": "iam",
      "inwi": "inwi",
      "itissalat": "itissalat",
      "maroc telecom": "maroc telecom",
      "orange": "orange"
    }
  },
  {
    "id": 38,
    "name": "Ghana",
    "operators": {
      "any": "any",
      "airtel": "airtel",
      "glomobile": "glomobile",
      "millicom": "millicom",
      "mtn": "mtn",
      "vodafone": "vodafone"
    }
  },
  {
    "id": 39,
    "name": "Argentina",
    "operators": {
      "any": "any",
      "claro": "claro",
      "movistar": "movistar",
      "nextel": "nextel",
      "personal": "personal",
      "tuenti": "tuenti"
    }
  },
  {
    "id": 40,
    "name": "Uzbekistan",
    "operators": {
      "any": "any",
      "beeline": "beeline",
      "humans": "humans",
      "mobiuz": "mobiuz",
      "mts": "mts",
      "perfectum": "perfectum",
      "ucell": "ucell",
      "ums": "ums",
      "uzmobile": "uzmobile"
    }
  },
  {
    "id": 41,
    "name": "Cameroon",
    "operators": {
      "any": "any",
      "mtn": "mtn",
      "nexttel": "nexttel",
      "orange": "orange"
    }
  },
  {
    "id": 42,
    "name": "Chad",
    "operators": {
      "any": "any",
      "airtel": "airtel",
      "salam": "salam",
      "tigo": "tigo"
    }
  },
  {
    "id": 43,
    "name": "Germany",
    "operators": {
      "any": "any",
      "fonic": "fonic",
      "lebara": "lebara",
      "lycamobile": "lycamobile",
      "o2": "o2",
      "ortel_mobile": "ortel_mobile",
      "telekom": "telekom",
      "vodafone": "vodafone"
    }
  },
  {
    "id": 44,
    "name": "Lithuania",
    "operators": {
      "any": "any",
      "bite": "bite",
      "labas": "labas",
      "pylduk": "pylduk",
      "tele2": "tele2",
      "telia": "telia"
    }
  },
  {
    "id": 45,
    "name": "Croatia",
    "operators": {
      "any": "any",
      "a1": "a1",
      "bonbon": "bonbon",
      "hrvatski telekom": "hrvatski telekom",
      "tele2": "tele2",
      "telemach": "telemach",
      "tmobile": "tmobile",
      "tomato": "tomato"
    }
  },
  {
    "id": 46,
    "name": "Sweden",
    "operators": {
      "any": "any",
      "comviq": "comviq",
      "lycamobile": "lycamobile",
      "netmore": "netmore",
      "tele2": "tele2",
      "telenor": "telenor",
      "telia": "telia",
      "three": "three",
      "vectone": "vectone",
      "vodafone": "vodafone"
    }
  },
  {
    "id": 47,
    "name": "Iraq",
    "operators": {
      "any": "any",
      "asiacell": "asiacell",
      "korek": "korek",
      "zain": "zain"
    }
  },
  {
    "id": 48,
    "name": "Netherlands",
    "operators": {
      "any": "any",
      "kpn": "kpn",
      "l_mobi": "l_mobi",
      "lebara": "lebara",
      "lmobiel": "lmobiel",
      "lycamobile": "lycamobile",
      "tmobile": "tmobile",
      "vodafone": "vodafone"
    }
  },
  {
    "id": 49,
    "name": "Latvia",
    "operators": {
      "any": "any",
      "bite": "bite",
      "lmt": "lmt",
      "pylduk": "pylduk",
      "tele2": "tele2",
      "xomobile": "xomobile",
      "zelta zivtina": "zelta zivtina"
    }
  },
  {
    "id": 50,
    "name": "Austria",
    "operators": {
      "any": "any",
      "a1": "a1",
      "eety": "eety",
      "hot_mobile": "hot_mobile",
      "lidl": "lidl",
      "lycamobile": "lycamobile",
      "magenta": "magenta",
      "orange": "orange",
      "telering": "telering",
      "three": "three",
      "tmobile": "tmobile",
      "wowww": "wowww",
      "yesss": "yesss"
    }
  },
  {
    "id": 51,
    "name": "Belarus",
    "operators": {
      "any": "any",
      "best": "best",
      "life": "life",
      "mdc": "mdc",
      "mts": "mts"
    }
  },
  {
    "id": 52,
    "name": "Thailand",
    "operators": {
      "any": "any",
      "ais": "ais",
      "cat_mobile": "cat_mobile",
      "dtac": "dtac",
      "my": "my",
      "truemove": "truemove"
    }
  },
  {
    "id": 53,
    "name": "Saudi Arabia",
    "operators": {
      "any": "any",
      "digitel": "digitel"
    }
  },
  {
    "id": 54,
    "name": "Mexico",
    "operators": {
      "any": "any",
      "movistar": "movistar",
      "telcel": "telcel"
    }
  },
  {
    "id": 55,
    "name": "Taiwan",
    "operators": {
      "any": "any",
      "chunghwa": "chunghwa",
      "fareast": "fareast"
    }
  },
  {
    "id": 56,
    "name": "Spain",
    "operators": {
      "any": "any",
      "altecom": "altecom",
      "cube_movil": "cube_movil",
      "euskaltel": "euskaltel",
      "finetwork": "finetwork",
      "lebara": "lebara",
      "llamaya": "llamaya",
      "lycamobile": "lycamobile",
      "masmovil": "masmovil",
      "movistar": "movistar",
      "orange": "orange",
      "tmobile": "tmobile",
      "vodafone": "vodafone",
      "yoigo": "yoigo",
      "you_mobile": "you_mobile"
    }
  },
  {
    "id": 57,
    "name": "Iran",
    "operators": {
      "any": "any",
      "aptel": "aptel",
      "azartel": "azartel",
      "hamrah_e_aval": "hamrah_e_aval",
      "irancell": "irancell",
      "mtn": "mtn",
      "rightel": "rightel",
      "samantel": "samantel",
      "shatel": "shatel",
      "taliya": "taliya",
      "tci": "tci"
    }
  },
  {
    "id": 58,
    "name": "Algeria",
    "operators": {
      "any": "any",
      "djezzy": "djezzy",
      "mobilis": "mobilis",
      "ooredoo": "ooredoo"
    }
  },
  {
    "id": 59,
    "name": "Slovenia",
    "operators": {
      "any": "any",
      "a1": "a1",
      "t-2": "t-2",
      "telekom": "telekom",
      "telemach": "telemach"
    }
  },
  {
    "id": 60,
    "name": "Bangladesh",
    "operators": {
      "any": "any",
      "airtel": "airtel",
      "banglalink": "banglalink",
      "banglalion": "banglalion",
      "grameenphone": "grameenphone",
      "ollo": "ollo",
      "robi": "robi",
      "teletalk": "teletalk"
    }
  },
  {
    "id": 61,
    "name": "Senegal",
    "operators": {
      "any": "any",
      "expresso": "expresso",
      "free": "free",
      "orange": "orange"
    }
  },
  {
    "id": 62,
    "name": "Turkey",
    "operators": {
      "any": "any",
      "turk_telekom": "turk_telekom",
      "turkcell": "turkcell",
      "vodafone": "vodafone"
    }
  },
  {
    "id": 63,
    "name": "Czech Republic",
    "operators": {
      "any": "any",
      "CzechRepublic_Virtual": "CzechRepublic_Virtual",
      "kaktus": "kaktus",
      "nordic telecom": "nordic telecom",
      "o2": "o2",
      "szdc": "szdc",
      "tmobile": "tmobile",
      "vodafone": "vodafone"
    }
  },
  {
    "id": 64,
    "name": "Sri Lanka",
    "operators": {
      "any": "any",
      "airtel": "airtel",
      "dialog": "dialog",
      "etisalat": "etisalat",
      "hutch": "hutch",
      "lanka bell": "lanka bell",
      "mobitel": "mobitel",
      "slt": "slt",
      "sltmobitel": "sltmobitel"
    }
  },
  {
    "id": 65,
    "name": "Peru",
    "operators": {
      "any": "any",
      "bitel": "bitel",
      "claro": "claro",
      "entel": "entel",
      "movistar": "movistar"
    }
  },
  {
    "id": 66,
    "name": "Pakistan",
    "operators": {
      "any": "any",
      "charji": "charji",
      "jazz": "jazz",
      "ptcl": "ptcl",
      "sco": "sco",
      "sco mobile": "sco mobile",
      "telenor": "telenor",
      "ufone": "ufone",
      "zong": "zong"
    }
  },
  {
    "id": 67,
    "name": "New Zealand",
    "operators": {
      "any": "any",
      "2degree": "2degree",
      "one_nz": "one_nz",
      "skinny": "skinny",
      "spark": "spark",
      "vodafone": "vodafone",
      "warehouse": "warehouse"
    }
  },
  {
    "id": 68,
    "name": "Guinea",
    "operators": {
      "any": "any",
      "cellcom": "cellcom",
      "mtn": "mtn",
      "orange": "orange",
      "sotelgui": "sotelgui",
      "telecel": "telecel"
    }
  },
  {
    "id": 69,
    "name": "Mali",
    "operators": {
      "any": "any",
      "malitel": "malitel",
      "orange": "orange",
      "telecel": "telecel"
    }
  },
  {
    "id": 70,
    "name": "Venezuela",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 71,
    "name": "Ethiopia",
    "operators": {
      "any": "any",
      "mtn": "mtn",
      "safaricom": "safaricom"
    }
  },
  {
    "id": 72,
    "name": "Mongolia",
    "operators": {
      "any": "any",
      "beeline": "beeline"
    }
  },
  {
    "id": 73,
    "name": "Brazil",
    "operators": {
      "any": "any",
      "algartelecom": "algartelecom",
      "arqia": "arqia",
      "cellular": "cellular",
      "claro": "claro",
      "correios_celular": "correios_celular",
      "links_field": "links_field",
      "nlt": "nlt",
      "oi": "oi",
      "tim": "tim",
      "vivo": "vivo"
    }
  },
  {
    "id": 74,
    "name": "Afghanistan",
    "operators": {
      "any": "any",
      "salaam": "salaam"
    }
  },
  {
    "id": 75,
    "name": "Uganda",
    "operators": {
      "any": "any",
      "airtel": "airtel",
      "k2_telecom": "k2_telecom",
      "lycamobile": "lycamobile",
      "mtn": "mtn",
      "orange": "orange",
      "smart": "smart",
      "smile": "smile",
      "uganda_telecom": "uganda_telecom"
    }
  },
  {
    "id": 76,
    "name": "Angola",
    "operators": {
      "any": "any",
      "africel": "africel",
      "movicel": "movicel",
      "unitel": "unitel"
    }
  },
  {
    "id": 77,
    "name": "Cyprus",
    "operators": {
      "any": "any",
      "cablenet": "cablenet",
      "cyta": "cyta",
      "epic": "epic",
      "lemontel": "lemontel",
      "primetel": "primetel",
      "vectone": "vectone",
      "vodafone": "vodafone"
    }
  },
  {
    "id": 78,
    "name": "France",
    "operators": {
      "any": "any",
      "bouygues": "bouygues",
      "free": "free",
      "kena_mobile": "kena_mobile",
      "lebara": "lebara",
      "lycamobile": "lycamobile",
      "orange": "orange",
      "sfr": "sfr",
      "syma_mobile": "syma_mobile",
      "vectone": "vectone"
    }
  },
  {
    "id": 79,
    "name": "Guinea",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 80,
    "name": "Mozambique",
    "operators": {
      "any": "any",
      "mcell": "mcell",
      "movitel": "movitel",
      "tmcel": "tmcel",
      "vodacom": "vodacom"
    }
  },
  {
    "id": 81,
    "name": "Nepal",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 82,
    "name": "Belgium",
    "operators": {
      "any": "any",
      "bandwidth": "bandwidth",
      "base": "base",
      "infrabel": "infrabel",
      "lycamobile": "lycamobile",
      "nethys": "nethys",
      "orange": "orange",
      "proximus": "proximus",
      "vectone": "vectone"
    }
  },
  {
    "id": 83,
    "name": "Bulgaria",
    "operators": {
      "any": "any",
      "a1": "a1",
      "bulsatcom": "bulsatcom",
      "max telecom": "max telecom",
      "telenor": "telenor",
      "vivacom": "vivacom",
      "yettel": "yettel"
    }
  },
  {
    "id": 84,
    "name": "Hungary",
    "operators": {
      "any": "any",
      "tmobile": "tmobile",
      "vodafone": "vodafone",
      "yettel": "yettel"
    }
  },
  {
    "id": 85,
    "name": "Moldova",
    "operators": {
      "any": "any",
      "idc": "idc",
      "moldcell": "moldcell",
      "Moldovia_Virtual": "Moldovia_Virtual",
      "orange": "orange",
      "unite": "unite"
    }
  },
  {
    "id": 86,
    "name": "Italy",
    "operators": {
      "any": "any",
      "digi": "digi",
      "ho": "ho",
      "iliad": "iliad",
      "kena_mobile": "kena_mobile",
      "lycamobile": "lycamobile",
      "nt_mobile": "nt_mobile",
      "optima": "optima",
      "syma_mobile": "syma_mobile",
      "tim": "tim",
      "vodafone": "vodafone",
      "wind": "wind"
    }
  },
  {
    "id": 87,
    "name": "Paraguay",
    "operators": {
      "any": "any",
      "claro": "claro",
      "personal": "personal"
    }
  },
  {
    "id": 88,
    "name": "Honduras",
    "operators": {
      "any": "any",
      "claro": "claro"
    }
  },
  {
    "id": 89,
    "name": "Tunisia",
    "operators": {
      "any": "any",
      "ooredoo": "ooredoo",
      "orange": "orange",
      "tunicell": "tunicell"
    }
  },
  {
    "id": 90,
    "name": "Nicaragua",
    "operators": {
      "any": "any",
      "movistar": "movistar"
    }
  },
  {
    "id": 91,
    "name": "Timor-Leste",
    "operators": {
      "any": "any",
      "telemor": "telemor",
      "telkomcel": "telkomcel",
      "timor_telecom": "timor_telecom"
    }
  },
  {
    "id": 92,
    "name": "Bolivia",
    "operators": {
      "any": "any",
      "tigo": "tigo",
      "viva": "viva"
    }
  },
  {
    "id": 93,
    "name": "Costa Rica",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 94,
    "name": "Guatemala",
    "operators": {
      "any": "any",
      "claro": "claro",
      "movistar": "movistar",
      "tigo": "tigo"
    }
  },
  {
    "id": 95,
    "name": "UNITED ARAB EMIRATES",
    "operators": {
      "any": "any",
      "du": "du"
    }
  },
  {
    "id": 96,
    "name": "Zimbabwe",
    "operators": {
      "any": "any",
      "econet": "econet",
      "netone": "netone",
      "telecel": "telecel"
    }
  },
  {
    "id": 97,
    "name": "Puerto Rico",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 98,
    "name": "Sudan",
    "operators": {
      "any": "any",
      "mtn": "mtn",
      "sudani_one": "sudani_one",
      "zain": "zain"
    }
  },
  {
    "id": 99,
    "name": "Togo",
    "operators": {
      "any": "any",
      "moov": "moov"
    }
  },
  {
    "id": 100,
    "name": "Kuwait",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 101,
    "name": "El Salvador",
    "operators": {
      "any": "any",
      "claro": "claro",
      "digi": "digi",
      "movistar": "movistar",
      "red": "red",
      "tigo": "tigo"
    }
  },
  {
    "id": 102,
    "name": "Libya",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 103,
    "name": "Jamaica",
    "operators": {
      "any": "any",
      "digi": "digi"
    }
  },
  {
    "id": 104,
    "name": "Trinidad and Tobago",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 105,
    "name": "Ecuador",
    "operators": {
      "any": "any",
      "claro": "claro",
      "cnt_mobile": "cnt_mobile",
      "movistar": "movistar",
      "tuenti": "tuenti"
    }
  },
  {
    "id": 106,
    "name": "Swaziland",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 107,
    "name": "Oman",
    "operators": {
      "any": "any",
      "omantel": "omantel",
      "ooredoo": "ooredoo"
    }
  },
  {
    "id": 108,
    "name": "Bosnia and Herzegovina",
    "operators": {
      "any": "any",
      "a1": "a1",
      "bh_telecom": "bh_telecom",
      "hej": "hej"
    }
  },
  {
    "id": 109,
    "name": "Dominican Republic",
    "operators": {
      "any": "any",
      "altice": "altice",
      "claro": "claro",
      "viva": "viva"
    }
  },
  {
    "id": 111,
    "name": "Qatar",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 112,
    "name": "Panama",
    "operators": {
      "any": "any",
      "masmovil": "masmovil"
    }
  },
  {
    "id": 113,
    "name": "Cuba",
    "operators": {
      "any": "any",
      "cubacel": "cubacel"
    }
  },
  {
    "id": 114,
    "name": "Mauritania",
    "operators": {
      "any": "any",
      "chinguitel": "chinguitel",
      "mattel": "mattel",
      "mauritel": "mauritel"
    }
  },
  {
    "id": 115,
    "name": "Sierra Leone",
    "operators": {
      "any": "any",
      "africel": "africel",
      "airtel": "airtel",
      "orange": "orange",
      "qcell": "qcell",
      "sierratel": "sierratel"
    }
  },
  {
    "id": 116,
    "name": "Jordan",
    "operators": {
      "any": "any",
      "orange": "orange",
      "umniah": "umniah",
      "xpress": "xpress",
      "zain": "zain"
    }
  },
  {
    "id": 117,
    "name": "Portugal",
    "operators": {
      "any": "any",
      "lebara": "lebara",
      "lycamobile": "lycamobile",
      "nos": "nos",
      "vodafone": "vodafone"
    }
  },
  {
    "id": 118,
    "name": "Barbados",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 119,
    "name": "Burundi",
    "operators": {
      "any": "any",
      "africel": "africel",
      "econet": "econet",
      "lacell": "lacell",
      "telecel": "telecel",
      "viettel": "viettel"
    }
  },
  {
    "id": 120,
    "name": "Benin",
    "operators": {
      "any": "any",
      "airtel": "airtel",
      "mtn": "mtn"
    }
  },
  {
    "id": 121,
    "name": "Brunei",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 122,
    "name": "Bahamas",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 123,
    "name": "Botswana",
    "operators": {
      "any": "any",
      "be_mobile": "be_mobile",
      "mascom": "mascom",
      "orange": "orange"
    }
  },
  {
    "id": 124,
    "name": "Belize",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 125,
    "name": "CAR",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 126,
    "name": "Dominica",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 127,
    "name": "Grenada",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 128,
    "name": "Georgia",
    "operators": {
      "any": "any",
      "beeline": "beeline",
      "geocell": "geocell",
      "hamrah_e_aval": "hamrah_e_aval",
      "magticom": "magticom",
      "silknet": "silknet"
    }
  },
  {
    "id": 129,
    "name": "Greece",
    "operators": {
      "any": "any",
      "cosmote": "cosmote",
      "cyta": "cyta",
      "ose": "ose",
      "q_telecom": "q_telecom",
      "vodafone": "vodafone",
      "wind": "wind"
    }
  },
  {
    "id": 130,
    "name": "Guinea-Bissau",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 131,
    "name": "Guyana",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 132,
    "name": "Iceland",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 133,
    "name": "Comoros",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 134,
    "name": "St. Kitts and Nevis",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 135,
    "name": "Liberia",
    "operators": {
      "any": "any",
      "cellcom": "cellcom",
      "comium": "comium",
      "libercell": "libercell",
      "libtelco": "libtelco",
      "lonestar": "lonestar"
    }
  },
  {
    "id": 136,
    "name": "Lesotho",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 137,
    "name": "Malawi",
    "operators": {
      "any": "any",
      "access": "access",
      "airtel": "airtel",
      "tnm": "tnm"
    }
  },
  {
    "id": 138,
    "name": "Namibia",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 139,
    "name": "Niger",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 140,
    "name": "Rwanda",
    "operators": {
      "any": "any",
      "airtel": "airtel",
      "mtn": "mtn"
    }
  },
  {
    "id": 141,
    "name": "Slovakia",
    "operators": {
      "any": "any",
      "4ka": "4ka",
      "o2": "o2",
      "orange": "orange",
      "telekom": "telekom"
    }
  },
  {
    "id": 142,
    "name": "Suriname",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 143,
    "name": "Tajikistan",
    "operators": {
      "any": "any",
      "babilon mobile": "babilon mobile",
      "beeline": "beeline",
      "indigo": "indigo",
      "megafon": "megafon",
      "tcell": "tcell"
    }
  },
  {
    "id": 144,
    "name": "Monaco",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 145,
    "name": "Bahrain",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 146,
    "name": "Reunion",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 147,
    "name": "Zambia",
    "operators": {
      "any": "any",
      "airtel": "airtel",
      "mtn": "mtn",
      "zamtel": "zamtel"
    }
  },
  {
    "id": 148,
    "name": "Armenia",
    "operators": {
      "any": "any",
      "team": "team",
      "viva": "viva",
      "vivo": "vivo"
    }
  },
  {
    "id": 149,
    "name": "Somalia",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 150,
    "name": "Congo",
    "operators": {
      "any": "any",
      "airtel": "airtel"
    }
  },
  {
    "id": 151,
    "name": "Chile",
    "operators": {
      "any": "any",
      "claro": "claro",
      "entel": "entel",
      "movistar": "movistar",
      "vodafone": "vodafone",
      "wom": "wom"
    }
  },
  {
    "id": 152,
    "name": "Burkina Faso",
    "operators": {
      "any": "any",
      "airtel": "airtel",
      "onatel": "onatel",
      "telecel": "telecel"
    }
  },
  {
    "id": 153,
    "name": "Lebanon",
    "operators": {
      "any": "any",
      "alfa": "alfa",
      "ogero": "ogero",
      "touch": "touch"
    }
  },
  {
    "id": 154,
    "name": "Gabon",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 155,
    "name": "Albania",
    "operators": {
      "any": "any",
      "telekom": "telekom",
      "vodafone": "vodafone"
    }
  },
  {
    "id": 156,
    "name": "Uruguay",
    "operators": {
      "any": "any",
      "antel": "antel",
      "claro": "claro"
    }
  },
  {
    "id": 157,
    "name": "Mauritius",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 158,
    "name": "Bhutan",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 159,
    "name": "Maldives",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 160,
    "name": "Guadeloupe",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 161,
    "name": "Turkmenistan",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 162,
    "name": "French Guiana",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 163,
    "name": "Finland",
    "operators": {
      "any": "any",
      "dna": "dna",
      "elisa": "elisa",
      "telia": "telia"
    }
  },
  {
    "id": 164,
    "name": "St. Lucia",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 165,
    "name": "Luxembourg",
    "operators": {
      "any": "any",
      "tango": "tango",
      "tiptop": "tiptop"
    }
  },
  {
    "id": 166,
    "name": "Saint Pierre and Miquelon",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 167,
    "name": "Equatorial Guinea",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 168,
    "name": "Djibouti",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 169,
    "name": "Saint Kitts and Nevis",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 170,
    "name": "Cayman Islands",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 171,
    "name": "Montenegro",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 172,
    "name": "Denmark",
    "operators": {
      "any": "any",
      "lebara": "lebara",
      "lycamobile": "lycamobile",
      "tdc": "tdc",
      "telenor": "telenor",
      "telia": "telia",
      "three": "three"
    }
  },
  {
    "id": 173,
    "name": "Switzerland",
    "operators": {
      "any": "any",
      "lebara": "lebara"
    }
  },
  {
    "id": 174,
    "name": "Norway",
    "operators": {
      "any": "any",
      "lycamobile": "lycamobile",
      "my_call": "my_call",
      "telia": "telia"
    }
  },
  {
    "id": 175,
    "name": "Australia",
    "operators": {
      "any": "any",
      "lebara": "lebara",
      "optus": "optus",
      "pivotel": "pivotel",
      "telstra": "telstra",
      "travelsim": "travelsim",
      "vodafone": "vodafone"
    }
  },
  {
    "id": 176,
    "name": "Eritrea",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 177,
    "name": "South Sudan",
    "operators": {
      "any": "any",
      "digitel": "digitel",
      "mtn": "mtn",
      "zain": "zain"
    }
  },
  {
    "id": 178,
    "name": "Sao Tome and Principe",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 179,
    "name": "Aruba",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 180,
    "name": "Montserrat",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 181,
    "name": "Anguilla",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 183,
    "name": "Northern Macedonia",
    "operators": {
      "any": "any",
      "a1": "a1",
      "lycamobile": "lycamobile",
      "telekom": "telekom",
      "vip": "vip"
    }
  },
  {
    "id": 184,
    "name": "Republic of Seychelles",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 185,
    "name": "New Caledonia",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 186,
    "name": "Cape Verde",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 187,
    "name": "USA (Real)",
    "operators": {
      "any": "any",
      "at_t": "at_t",
      "boost_mobile": "boost_mobile",
      "cricket_wireless": "cricket_wireless",
      "h2o_wireless": "h2o_wireless",
      "hello_mobile": "hello_mobile",
      "joltmobile": "joltmobile",
      "lycamobile": "lycamobile",
      "mint_mobile": "mint_mobile",
      "moabits": "moabits",
      "physic": "physic",
      "textnow": "textnow",
      "tmobile": "tmobile",
      "ultra_mobile": "ultra_mobile",
      "us_mobile": "us_mobile"
    }
  },
  {
    "id": 188,
    "name": "Palestine",
    "operators": {
      "any": "any",
      "jawwal": "jawwal",
      "wataniya": "wataniya"
    }
  },
  {
    "id": 189,
    "name": "Fiji",
    "operators": {
      "any": "any",
      "vodafone": "vodafone"
    }
  },
  {
    "id": 190,
    "name": "South Korea",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 192,
    "name": "Western Sahara",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 193,
    "name": "Solomon Islands",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 196,
    "name": "Singapore",
    "operators": {
      "any": "any",
      "m1": "m1",
      "maxx": "maxx",
      "simba": "simba",
      "singtel": "singtel",
      "starhub": "starhub"
    }
  },
  {
    "id": 197,
    "name": "Tonga",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 198,
    "name": "American Samoa",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 199,
    "name": "Malta",
    "operators": {
      "any": "any",
      "epic": "epic",
      "go": "go",
      "melita": "melita"
    }
  },
  {
    "id": 666,
    "name": "Gibraltar",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 668,
    "name": "Bermuda",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 670,
    "name": "Japan",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 672,
    "name": "Syria",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 673,
    "name": "Faroe Islands",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 674,
    "name": "Martinique",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 675,
    "name": "Turks and Caicos Islands",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 676,
    "name": "St. Barthélemy",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 678,
    "name": "Nauru",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 680,
    "name": "Curaçao",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 681,
    "name": "Samoa",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 682,
    "name": "Vanuatu",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 683,
    "name": "Greenland",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 684,
    "name": "Kosovo",
    "operators": {
      "any": "any",
      "ipko": "ipko",
      "mtc": "mtc",
      "vala": "vala"
    }
  },
  {
    "id": 685,
    "name": "Liechtenstein",
    "operators": {
      "any": "any"
    }
  },
  {
    "id": 686,
    "name": "Sint Maarten",
    "operators": {
      "any": "any"
    }
  }
]
            
####### do not uncomment for below code ###############################################
# from sms_activation_service import SmsActivationService
# Number5Sim_obj = SmsActivationService()
# print(Number5Sim_obj)
# number = Number5Sim_obj.get_number(country='india', operator='any', product='yahoo')
# print(number)
# status = Number5Sim_obj.cancel_order()
# print(status)

#######################################################################################

# https://sms-activation-service.pro/stubs/handler_api?api_key=e7981c679393a85284ac0ad45f0d222b&lang=en&action=getNumber&service=1415&operator=any&country=22
	