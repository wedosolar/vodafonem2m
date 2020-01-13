# GNU GENERAL PUBLIC LICENSE
# Author: James Bowler
# vodafonem2m.py
# 30/10/2019


from datetime import datetime

import requests
import base64

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
                 api_url="https://api.m2m.vodafone.com"):
        """
        Create an instance of the VodafoneM2M class.

        :param username: (str): The users username.
        :param password: (str): The users password.
        :param client_id: (str): Application Consumer Key obtained from your operator.
        :param client_secret: (str): Application Consumer Secret obtained from your operator.
        :param api_url: (str) url

        """
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
        concat_string = "{}:{}".format(username, password).encode('utf-8')
        encoded_string = base64.standard_b64encode(concat_string).decode('utf-8')
        headers = {
            'Authorization': "Basic " + encoded_string,
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
        data = string.format(client_id=self.__client_id, client_secret=self.__client_secret, scope=self.scope)
        self.token = self._send_message('post', '/m2m/v1/oauth2/access-token', data=data, headers=headers)
        self.token['utc_timestamp'] = datetime.utcnow()

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
    def _handle_api_response(response):
        """
        Throw exceptions on errors from API.

        :param response:
        :return:
        """
        if not response:
            raise ValueError('Error getting data from the api, no data returned')

        response.raise_for_status()

        return response.json()

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
        if not headers:
            headers = {'Authorization': "Bearer {}".format(self.token['access_token'])}
        url = self.url + endpoint
        r = self.session.request(method, url, data=data,
                                 params=params, headers=headers)
        return self._handle_api_response(r)
