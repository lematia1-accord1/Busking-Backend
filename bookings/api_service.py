import requests
from requests.exceptions import RequestException

class APIService:
    BASE_URL = 'https://api.easypay.ug'
    ENDPOINT = '/endpoint'
    
    def __init__(self, access_token):
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

    def make_api_request(self, data):
        """
        Make a POST request to the EasyPay API and return the response.

        Args:
            data (dict): The request payload to send to the API.

        Returns:
            dict: The JSON response from the API if successful.

        Raises:
            Exception: If the request fails or returns a non-200 status code.
        """
        url = f'{self.BASE_URL}{self.ENDPOINT}'

        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            return response.json()

        except RequestException as e:
            raise Exception(f'API request failed: {str(e)}')
        except ValueError:
            raise Exception('Invalid JSON response from the API.')

