'''
Created on 08.08.2015

@author: Djuro Drljaca
'''

import requests
import json
import enum
import urllib.parse

# Public -------------------------------------------------------------------------------------------

class CertificateVerification(enum.Enum):
    '''
    Certificate verification
    '''
    Disabled = 0
    Enabled = 1

class Connection(object):
    '''
    Connection to the server.
    
    During login the REST API URL, authentication parameters and certificate verificatin options are
    supplied. After a successful login HTTP methods (DELETE, GET, POST) can be called
    and this class will prepare all the data needed to successfully call the method.
    
    The data that will be prepared is:
    * the full URL for the method (base URL combined with relative URL and additional parameters)
    * authentication parameters (authentication ID and token)
    * other options (certificate verification)
    
    Below are some examples of URL's mentioned above.
        
    Example without parameters:
    * base URL:     "https://tuleap.example.com:443/api"
    * relative URL: "/tokens"
    * full URL:     "https://tuleap.example.com:443/api/tokens"
    
    Example with single parameter:
    * base URL:     "https://tuleap.example.com:443/api"
    * relative URL: "/projects"
    * parameters:   {"limit": 10}
    * full URL:     "https://tuleap.example.com:443/api/projects?limit=10"
    
    Example with multiple parameters:
    * base URL:     "https://tuleap.example.com:443/api"
    * relative URL: "/projects"
    * parameters:   {"limit": 10, "offset": 50}
    * full URL:     "https://tuleap.example.com:443/api/projects?limit=10&offest=50"
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        self._Clear()
    
    def IsLoggedIn(self):
        '''
        Check if logged in
        
        :return: Success or failure
        :rtype: bool
        '''
        return self._isLoggedIn
    
    def Login(self,
              baseUrl,
              username,
              password,
              certificateVerification = CertificateVerification.Enabled):
        '''
        Log in to the selected Tuleap instance
        
        :param baseUrl: URL of the selected Tuleap instance
                        (example: https://tuleap.example.com:443/api)
        :type baseUrl: string
        
        :param username: User name
        :type username: string
        
        :param password: Password
        :type password: string
        
        :param certificateVerification: Enable or disable certificate verification
        :type certificateVerification: CertificateVerification
        
        :return: success: Success or failure, errorInfo: Error info
        :rtype: (bool, ErrorInfo)
        '''
        # Clear last response message
        self._lastResponseMessage = None
        
        # Log out if already logged in
        if self.IsLoggedIn():
            self.Logout()
        
        # Get login token
        url = baseUrl + "/tokens"
        data = {"username": username, "password": password}
        verifyCertificate = (certificateVerification == CertificateVerification.Enabled)
        
        response = requests.post(url, data=data, verify=verifyCertificate)
        self._lastResponseMessage = response
        
        # Parse response
        success = self._loginToken.Parse(response)
        
        if success:
            # Save connection to the server
            self._baseUrl = baseUrl
            self._isLoggedIn = True
            self._verifyCertificate = verifyCertificate
            self._authenticationHeaders = {"X-Auth-Token": self._loginToken.token,
                                           "X-Auth-UserId": self._loginToken.userId}
            success = True
        
        return success
    
    def Logout(self):
        '''
        Log out of the connected Tuleap instance
        
        :return: success: Success or failure
        :rtype: bool
        '''
        # Clear last response message
        self._lastResponseMessage = None
        
        # Check if logged in
        if not self.IsLoggedIn():
            # Not logged in
            return True
        
        # Logout (delete login token)
        relativeUrl = "tokens/{:}".format(self._loginToken.token)
        
        success = self.CallDeleteMethod(relativeUrl)
        
        # Clean up after logout
        self._Clear()
        
        return success
    
    def CallDeleteMethod(self, relativeUrl, parameters = {}, successStatusCodes = [200]):
        '''
        Call DELETE method on the server
        
        :param relativeUrl: relative part of URL
        :type relativeUrl: string
        
        :param parameters: parameters that should be added to the URL
        :type parameters: dict
        
        :param successStatusCodes: list of HTTP status codes that represent 'success'
        :type successStatusCodes: list[int]
        
        :return: Success or failure
        :rtype: bool
        
        :note: Do not forget to add the leading '/' in the relative URL!
        '''
        # Clear last response message
        self._lastResponseMessage = None
        
        # Check if logged in
        if not self.IsLoggedIn():
            return False
        
        # Check for leading '/' in the relative URL
        if not relativeUrl.startswith("/"):
            return False
        
        # Call the DELETE method
        success = False
        url = self._CreateFullUrl(relativeUrl, parameters)
        
        response = requests.delete(url,
                                   headers=self._connection.headers,
                                   verify=self._connection.verifyCertificate)
        self._lastResponseMessage = response
        
        # Check for success
        if (response.status_code in successStatusCodes):
            success = True
        
        return success
    
    def CallGetMethod(self, relativeUrl, parameters = {}, successStatusCodes = [200]):
        '''
        Call GET method on the server
        
        :param relativeUrl: relative part of URL
        :type relativeUrl: string
        
        :param parameters: parameters that should be added to the URL
        :type parameters: dict
        
        :param successStatusCodes: list of HTTP status codes that represent 'success'
        :type successStatusCodes: list[int]
        
        :return: Success or failure
        :rtype: bool
        
        :note: Do not forget to add the leading '/' in the relative URL!
        '''
        # Clear last response message
        self._lastResponseMessage = None
        
        # Check if logged in
        if not self.IsLoggedIn():
            return False
        
        # Check for leading '/' in the relative URL
        if not relativeUrl.startswith("/"):
            return False
        
        # Call the GET method
        success = False
        url = self._CreateFullUrl(relativeUrl, parameters)
        
        response = requests.get(url,
                                headers=self._connection.headers,
                                verify=self._connection.verifyCertificate)
        self._lastResponseMessage = response
        
        # Check for success
        if (response.status_code in successStatusCodes):
            success = True
        
        return success
    
    def CallPostMethod(self, relativeUrl, data = {}, successStatusCodes = [200]):
        '''
        Call POST method on the server
        
        :param relativeUrl: relative part of URL
        :type relativeUrl: string
        
        :param data: request data
        :type data: dict
        
        :param successStatusCodes: list of HTTP status codes that represent 'success'
        :type successStatusCodes: list[int]
        
        :return: Success or failure
        :rtype: bool
        
        :note: Do not forget to add the leading '/' in the relative URL!
        '''
        # Clear last response message
        self._lastResponseMessage = None
        
        # Check if logged in
        if not self.IsLoggedIn():
            return False
        
        # Check for leading '/' in the relative URL
        if not relativeUrl.startswith("/"):
            return False
        
        # Call the POST method
        success = False
        url = self._CreateFullUrl(relativeUrl)
        
        response = requests.post(url,
                                 data=data,
                                 headers=self._connection.headers,
                                 verify=self._connection.verifyCertificate)
        self._lastResponseMessage = response
        
        # Check for success
        if (response.status_code in successStatusCodes):
            success = True
        
        return success
    
    def GetLastResponseMessage(self):
        '''
        Get last response message
        
        :return: Last response message
        :rtype: requests.Response
        
        :note: This could be useful for diagnostic purposes when an error occurs
        '''
        return self._lastResponseMessage.request
    
    def _CreateFullUrl(self, relativeUrl, parameters = {}):
        '''
        Create "full" URL from a "relative" URL. "Full" URL is created by combining REST API URL
        with "relative" URL and optional parameters.
        
        :param relativeUrl: relative part of URL
        :type relativeUrl: string
        
        :param parameters: parameters that should be appended to the URL
        :type parameters: dict()
        
        :return: Full URL
        :rtype: string
        '''
        url = self._baseUrl + relativeUrl
        
        if (len(parameters) > 0):
            url = url + "?%s" % urllib.parse.urlencode(parameters)
        
        return url
    
    def _Clear(self):
        '''
        Clear all members
        '''
        self._isLoggedIn = False
        self._baseUrl = ""
        self._loginToken = _LoginToken()
        self._verifyCertificate = True
        self._authenticationHeaders = None
        self._lastResponseMessage = None

# Private ------------------------------------------------------------------------------------------

class _LoginToken(object):
    '''
    Login token
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        self.userId = ""
        self.token = ""
    
    def Parse(self, response):
        '''
        Parse response object for login data
        
        :param response: Response message from server
        :type response: requests.Response
        
        :return: Success or failure
        :rtype: bool
        '''
        success = False
        
        if (response.status_code == 200):
            responseData = json.loads(response.text)
            
            # Save login token
            userId = responseData["user_id"]
            token = responseData["token"]
            
            self.userId = userId
            self.token = token
            success = True
        
        return success















        