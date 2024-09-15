import requests
from django.conf import settings
from requests.exceptions import RequestException

class EasyPayMobileMoney:
    def __init__(self):
        self.api_key = settings.EASYPAY_MOBILE_MONEY_API_KEY
        self.api_url = settings.EASYPAY_MOBILE_MONEY_API_URL
        self.headers = {'Authorization': f'Bearer {self.api_key}'}

    def initiate_transaction(self, phone_number, amount, transaction_id, description):
        """
        Initiate a mobile money transaction with EasyPay.

        Args:
            phone_number (str): The recipient's phone number.
            amount (float): The amount to be transferred.
            transaction_id (str): The unique ID for the transaction.
            description (str): A description of the transaction.

        Returns:
            dict: The API response in JSON format.

        Raises:
            Exception: If the request fails or returns an error.
        """
        url = f"{self.api_url}/initiate"
        payload = {
            'phone_number': phone_number,
            'amount': amount,
            'transaction_id': transaction_id,
            'description': description,
        }
        return self._post_request(url, payload)

    def check_transaction_status(self, transaction_id):
        """
        Check the status of a mobile money transaction.

        Args:
            transaction_id (str): The unique ID of the transaction.

        Returns:
            dict: The API response in JSON format.

        Raises:
            Exception: If the request fails or returns an error.
        """
        url = f"{self.api_url}/status/{transaction_id}"
        return self._get_request(url)

    def refund_transaction(self, transaction_id):
        """
        Initiate a refund for a mobile money transaction.

        Args:
            transaction_id (str): The unique ID of the transaction to be refunded.

        Returns:
            dict: The API response in JSON format.

        Raises:
            Exception: If the request fails or returns an error.
        """
        url = f"{self.api_url}/refund"
        payload = {'transaction_id': transaction_id}
        return self._post_request(url, payload)

    def _post_request(self, url, payload):
        """
        Helper method to make a POST request to the API.

        Args:
            url (str): The API endpoint URL.
            payload (dict): The data to be sent in the POST request.

        Returns:
            dict: The API response in JSON format.

        Raises:
            Exception: If the request fails or returns an error.
        """
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except ValueError:
            raise Exception("Invalid JSON response from the API.")

    def _get_request(self, url):
        """
        Helper method to make a GET request to the API.

        Args:
            url (str): The API endpoint URL.

        Returns:
            dict: The API response in JSON format.

        Raises:
            Exception: If the request fails or returns an error.
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except ValueError:
            raise Exception("Invalid JSON response from the API.")
