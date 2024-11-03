import requests
import json
from django.conf import settings
from requests.exceptions import RequestException
from urllib3.exceptions import InsecureRequestWarning
import warnings


class EasyPayMobileMoney:
    def __init__(self):
        self.api_key = settings.EASYPAY_MOBILE_MONEY_API_KEY
        self.api_url = settings.EASYPAY_MOBILE_MONEY_API_URL
        self.headers = {'Authorization': f'Bearer {self.api_key}'}
        self.client_id = settings.EASYPAY_CLIENT_ID
        self.client_secret = settings.EASYPAY_CLIENT_SECRET

    def initiate_transaction(self, phone_number, amount, transaction_id, description):
        return self.initiate_payment(phone_number, amount, transaction_id, description)

    def initiate_payment(self, phone_number, amount, transaction_id, description):
        url = f'https://www.easypay.co.ug/api/'
        payload = {
            'username': self.client_id,
            'password': self.client_secret,
            'action': 'mmdeposit',
            'amount': amount,
            'phone': phone_number,
            'currency': 'UGX',
            'reference': transaction_id,
            'reason': description,
        }

        try:
            response = requests.post(
                url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=400,
                verify=False
            )
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except ValueError:
            raise Exception("Invalid JSON response from the API.")

    def check_transaction_status(self, transaction_id):
        url = f"{self.api_url}/status/{transaction_id}"
        return self._get_request(url)

    def refund_transaction(self, transaction_id):
        url = f"{self.api_url}/refund"
        payload = {'transaction_id': transaction_id}
        return self._post_request(url, payload)

    def _post_request(self, url, payload):
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except ValueError:
            raise Exception("Invalid JSON response from the API.")

    def _get_request(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except ValueError:
            raise Exception("Invalid JSON response from the API.")

warnings.simplefilter('ignore', InsecureRequestWarning)

class EasyPayMobileMoney:
    def initiate_transaction(self, phone_number, amount, transaction_id, description):
        url = 'https://www.easypay.co.ug/api/endpoint'
        data = {
            'phone_number': phone_number,
            'amount': amount,
            'transaction_id': transaction_id,
            'description': description
        }

        response = requests.post(url, json=data, verify=True)

        if response.status_code == 200:
            return response.json()
        else:
            return {'error': response.text}
