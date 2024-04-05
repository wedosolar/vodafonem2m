# GNU GENERAL PUBLIC LICENSE
# Author: James Bowler
# vodafonem2m.py
# 30/10/2019


from datetime import datetime, timedelta
import base64
import requests

class VodafoneM2M:
    """
    Provides access to Vodafone M2M endpoints via the REST API.
    All requests default to the production `api_url`: 'https://api.m2m.vodafone.com'.
    Attributes:
        url (str): The api url for this client instance to use.
        session (requests.Session): Persistent HTTP connection object.
    """

    token = None
    home = None
    scope = None

    def __init__(self, username, password, client_id, client_secret,
                 api_url="https://api.m2m.vodafone.com", debug=False):
        """
        Create an instance of the VodafoneM2M class.

        :param username: (str): The users username.
        :param password: (str): The users password.
        :param client_id: (str): Application Consumer Key obtained from your operator.
        :param client_secret: (str): Application Consumer Secret obtained from your operator.
        :param api_url: (str) url

        """
        self.__username = username
        self.__password = password
        self.debug = debug
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.session = requests.Session()
        self.url = api_url
        self.set_auth_token(username, password)

    def set_auth_token(self, username, password):
        """
        Set the auth token.

        :param username:
        :param password:
        :return:
        """
        str_usernamepassword = f"{username}:{password}"
        b64_usernamepassword = base64.standard_b64encode(str_usernamepassword.encode('utf-8'))
        str_b64_usernamepassword = b64_usernamepassword.decode('utf-8')
        headers = {
            'Authorization': "Basic " + str_b64_usernamepassword,
            'Content-Type': "application/x-www-form-urlencoded",
            'Accept': "*/*",
            'Cache-Control': "no-cache",
            'Host': "api.m2m.vodafone.com",
            'Accept-Encoding': "gzip, deflate",
            'Content-Length': "125",
            'Connection': "keep-alive",
            'cache-control': "no-cache"
        }
        string = "grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}&scope={scope}"
        data = string.format(client_id=self.__client_id, client_secret=self.__client_secret, scope=f"{self.scope}")
        self.token = self._send_message('post', '/m2m/v1/oauth2/access-token', data=data, headers=headers)
        self.token['utc_timestamp'] = datetime.utcnow()

    def get_auth_token(self):
        """
        Gets the auth token, refreshing it if necessary.

        :return: The auth token.
        """
        if self.token is None or self._is_token_expired():
            self.set_auth_token(self.__username, self.__password)  # Refresh the token
        return self.token['access_token']

    def _is_token_expired(self):
        """
        Checks if the current auth token is expired.

        :return: True if the token is expired, False otherwise.
        """
        # Adjust to dynamically check based on the stored expiration
        token_expiry = self.token['utc_timestamp'] + timedelta(seconds=int(self.token['expires_in']))
        return datetime.utcnow() > token_expiry

    def get_home_document(self):
        """
        This is the top level resource that returns URIs to all other resources in this API.
        :return:

        {'links': {'self': {'href': 'https://dev-prd.api.m2m.vodafone.com/m2m/v1/devices'},
          'http://a42.vodafone.com/rels/a42/getDeviceDetails': {'href': 'https://dev-prd.api.m2m.vodafone.com/m2m/v1/devices/{deviceId}',
           'method': 'GET',
           'template': 'https://dev-prd.api.m2m.vodafone.com/m2m/v1/devices/{deviceId}',
           'type': 'application/vnd.vodafone.a42.m2m.devices+json'},
          'http://a42.vodafone.com/rels/a42/getDeviceHistoryV2 ': {'href': 'https://dev-prd.api.m2m.vodafone.com/m2m/v1/devices/{deviceId}/history',
           'method': 'GET',
           'template': 'https://dev-prd.api.m2m.vodafone.com/m2m/v1/devices/{deviceId}/history{?startDate,endDate,pageSize,pageNumber}',
           'type': 'application/vnd.vodafone.a42.m2m.devices+json'},
          'http://a42.vodafone.com/rels/a42/getDeviceRegistrationDetails': {'href': 'https://dev-prd.api.m2m.vodafone.com/m2m/v1/devices/{deviceId}/registration',
           'method': 'GET',
           'template': 'https://dev-prd.api.m2m.vodafone.com/m2m/v1/devices/{deviceId}/registration',
           'type': 'application/vnd.vodafone.a42.m2m.devices+json'}}}

        """
        return self._send_message('get', '/m2m/v1/{}'.format(self.home))

    @staticmethod
    def _handle_api_response(json_response):
        """
        Throw exceptions on errors from API.

        :param json_response:
        :return:
        """

        if not json_response:
            raise ValueError('Error getting data from the api, no data returned')

        if "error" in json_response:
            raise ValueError("Standard Error:: {} : {}".format(
                json_response["error"], json_response["error_description"]))
        elif "description" in json_response:
            if "Service Error" in json_response['description']:
                raise ValueError("Service Error:: {} : {}".format(
                    json_response["id"], json_response["description"]))
        else:
            try:
                codes = json_response[list(json_response.keys())[0]]['return']['returnCode']
                if codes['majorReturnCode'] != '000' or codes['minorReturnCode'] != '0000':
                    raise ValueError(
                            "Return Code Description:: {} Error:: Major: {}, Minor: {}".format(
                            codes['description'], codes['majorReturnCode'], codes['minorReturnCode'])
                    )
            except KeyError:
                pass
            except TypeError:
                pass
        return json_response

    def testing(self):
        endpoint = "/m2m/rest/v1/utility/httpPing"
        params = {"echo": "testing"}
        return self._send_message('get', endpoint, params=params)

    def _send_message(self, method, endpoint, params=None, headers=None, data=None):
        """
        Send API request.

        :param method:
        :param endpoint:
        :param params:
        :param headers:
        :param data:
        :return: dict

        """
        
        url = self.url + endpoint
        if self.debug:
            print(f"Sending {method} request to {url}: data: {data}, params: {params}, headers: {headers}")
        
        if not headers:
            headers = {
                'Authorization': "Bearer {}".format(self.get_auth_token()),
                'Content-Type': 'application/json',
                'accept': 'application/json'
            }
            r = self.session.request(method, url, json=data, params=params, headers=headers)
        else:
            r = self.session.request(method, url, data=data, params=params, headers=headers)

        json_response = r.json()
        if self.debug:
            print(f"Got response from Vodafone M2M API: {json_response}")

        return self._handle_api_response(json_response)
