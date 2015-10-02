"""
The MIT License (MIT)

Copyright (c) 2014 Trustly Group AB

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import httplib
import pkgutil
import types
import base64

from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA

import trustly.exceptions
import trustly.data.jsonrpcnotificationresponse
import trustly.data.jsonrpcnotificationrequest

class API(object):
        # Last  data object of last request made, this is primarily here for
        # debugging purpose or you for any other reason would like to know
        # exactly what data we did just send
    last_request = None

        # Basic key management, the actual key and the imported class
        # representation of the trustly keys used in the integration. All
        # signed calls coming from trustly will be verified using this key
    trustly_publickey = None
    trustly_verifyer = None

        # Connection information for the API backend
    api_host = None
    api_port = None
    api_is_https = None

    def __init__(self, host, port, is_https):
        self.api_host = host
        self.api_port = port
        self.api_is_https = bool(is_https)

        self.load_trustly_publickey()

    def load_trustly_publickey(self):
        trustly_pkey_str = None
        try:
            trustly_pkey_str = pkgutil.get_data('trustly.api', 'keys/{0}:{1}.public.pem'.format(self.api_host, self.api_port))
        except IOError as e:
            pass
        if trustly_pkey_str is None:
            trustly_pkey_str = pkgutil.get_data('trustly.api', 'keys/{0}.public.pem'.format(self.api_host))

        self.trustly_publickey = RSA.importKey(trustly_pkey_str)
        self.trustly_verifyer = PKCS1_v1_5.new(self.trustly_publickey)

    def serialize_data(self, data=None):
        ret = ''
        if type(data) == types.ListType:
            for k in sorted(data, key=lambda s: str(s)):
                ret = ret + self.serialize_data(k)
        elif type(data) == types.DictType:
            for k in sorted(data.keys(), key=lambda s: str(s)):
                ret = ret + k + self.serialize_data(data[k]) 
        elif data is not None:
            return unicode(data)
        return ret

    def _verify_trustly_signed_data(self, method, uuid, signature, data):
        if method is None:
            method = ''

        if uuid is None:
            uuid= ''

        if signature is None:
            return False

        decoded_signature = base64.b64decode(signature)
        plaintext = method + uuid + self.serialize_data(data)
        sha1hash = SHA.new(plaintext.encode('utf-8'))

        return self.trustly_verifyer.verify(sha1hash, decoded_signature)

    def verify_trustly_signed_response(self, response):
        method = response.get_method()
        uuid = response.get_uuid()
        signature = response.get_signature()
        data = response.get_data()

        return self._verify_trustly_signed_data(method, uuid, signature, data)

    def verify_trustly_signed_notification(self, notification):
        method = notification.get_method()
        uuid = notification.get_uuid()
        signature = notification.get_signature()
        data = notification.get_data()

        return self._verify_trustly_signed_data(method, uuid, signature, data)

    def set_host(host=None, port=None, is_https=None):
        if host is not None:
            self.api_host = host
            self.load_trustly_publickey()

        if port is not None:
            self.api_port = port

        if is_https is not None:
            self.api_is_https = is_https

        # Connect an http/https connection to the API and return the httplib
        # connection from the connect. Will raise TrustlyConnectionError if the
        # connection failed
    def connect(self):
        try:
            if self.api_is_https:
                call = httplib.HTTPSConnection(self.api_host, self.api_port)
            else:
                call = httplib.HTTPConnection(self.api_host, self.api_port)

        except Exception as e:
            raise trustly.exceptions.TrustlyConnectionError(str(e))

        return call

        # Return the base url for the api.
    def base_url(self):
        if self.api_is_https:
            if self.api_port == 443:
                url = 'https://{0}'.format(self.api_host)
            else:
                url = 'https://{0}:{1}'.format(self.api_host, self.api_port)
        else:
            if self.api_port == 80:
                url = 'http://{0}'.format(self.api_host)
            else:
                url = 'http://{0}:{1}'.format(self.api_host, self.api_port)

        return url

    def handle_notification(self, httpbody):
        request = trustly.data.jsonrpcnotificationrequest.JSONRPCNotificationRequest(httpbody) 

        if self.verify_trustly_signed_notification(request) != True:
            raise trustly.exceptions.TrustlySignatureError('Incoming notification signature is not valid', request)
        return request


    def notification_response(self, notification, success=True):
        response = trustly.data.jsonrpcnotificationresponse.JSONRPCNotificationResponse(notification, success)
        return response

        # Return the full API url
    def url(self, request=None):
        return '{0}{1}'.format(self.base_url(), self.url_path(request))

        # Return the path of the url
    def url_path(self, request=None):
        raise NotImplementedError()

        # Process the result after a successfull api call. Should return a
        # subclass of trustly.data.response.Response
    def handle_response(self, request, httpcall):
        raise NotImplementedError()

        # Insert the credentials needed for connecting to the API. This will
        # typically vary with the API in use.
    def insert_credentials(self, request):
        raise NotImplementedError()

        # Issue the call to the API given the data in a subclass of
        # trustly.data.request.Request. Before calling
        # self.insert_credentials() will be called to insert the appropriate
        # API credentials for the call. And self.handle_response() will be
        # called as a post processing of the result. Returns a subclass of
        # trustly.data.response.Response
    def call(self, request):
        self.insert_credentials(request)
        self.last_request = request

        jsonstr = request.json()

        url = self.url_path(request)
        try:
            call = self.connect()

            ret = call.request('POST', url, jsonstr)
        except trustly.exceptions.TrustlyConnectionError as e:
            raise
        except Exception as e:
            raise trustly.exceptions.TrustlyConnectionError(str(e))

        return self.handle_response(request, call)

        # Return the last trustly.data.request.Request class used to issue a
        # call. Useful for debugging data actually transmitted to trustly. 
        #
        # NOTE: This will contain bare login credentials, proper caution should
        # be done before dumping this to screen or a log file to ensure login
        # credentials are kept secret.
    def get_last_request(self):
        return self.last_request

        # Utility function for setting boolean values in the call based upon "real" python boolean values
    def api_bool(self, value):
        if value is not None:
            if value:
                return '1'
            else:
                return '0'
        return None

# vim: set et cindent ts=4 ts=4 sw=4:
