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

from __future__ import absolute_import
import json
import types
import pprint

import trustly.data.data
import trustly.exceptions

class Response(trustly.data.data.Data):
        # http response code and status from the actual call
    response_status = None
    response_reason = None
        # Full response body as read raw from the connection
    response_body = None
        # Shortcut to the result part of the response, will be pointed to the
        # data guts correctly for both errors and proper results respectivly
    response_result = None

        # Build a new response data object using the (not yet read) response
        # from a httplib call. JSON data from the call will be set in
        # self.payload. The raw response body in self.response_body,
        # self.response_status and self.response_reason will be http response
        # codes for the call.
        # If the call was not successful a TrustlyConnectionError() will be
        # raised. In this case the payload and response_body will not be
        # defined, response_status and response_reason will however be set to
        # the corresponding http responses
    def __init__(self, call):
        super(Response, self).__init__()

        resp = call.getresponse()

        self.response_status = resp.status
        self.response_reason = resp.reason

        body = self.response_body = resp.read()

        try:
            if isinstance(body, bytes):
                body = body.decode('utf8')

            payload = json.loads(body)
            if payload is not None:
                self.payload = payload
        except ValueError as e:
                # Only throw the connection error exception here if we did not 
                # receive a valid JSON response, if we did recive one we will use 
                # the error information in that response instead. 
            if self.response_status != 200:
                raise trustly.exceptions.TrustlyConnectionError('{0} {1}'.format(self.response_status, self.response_reason))
            else:
                raise trustly.exceptions.TrustlyDataError(str(e))

        try:
            self.response_result = self.get('result')
        except KeyError as e:
            pass

        if self.response_result is None:
            try:
                self.response_result = self.get('error')
            except KeyError as e:
                pass

        if self.response_result is None:
            raise trustly.exceptions.TrustlyDataError('No result or error in response {0}'.format(pprint.pformat(self.payload)))

        # Reveal wether or not the call resulted in an error. This will reveal the
        # JSON RPC response codes, not the actual http response. If the http
        # call failed, check out self.response_code for the http response code.
    def is_error(self):
        try:
            if self.get('error') is not None:
                return True
        except KeyError as e:
            return False

        # Reveal wether or not the call was successful. This will reveal the
        # JSON RPC response codes, not the actual http response. If the http
        # call failed, check out self.response_code for the http response code.
    def is_success(self):
        try:
            if self.get('result') is not None:
                return True
        except KeyError as e:
            return False

    def get_error_code(self):
        if self.is_error(): 
            return error.response_result.get('code')
        return None

    def get_error_message(self):
        if self.is_error(): 
            return error.response_result.get('message')
        return None

        # Returns the uuid field from the response, None if not found
    def get_uuid(self):
        return self.response_result.get('uuid')

        # Returns the method field from the response, None if not found
    def get_method(self):
        return self.response_result.get('method')

        # Returns the signature field from the response, None if not found
    def get_signature(self):
        return self.response_result.get('signature')

        # Return the result part of the response structure. If a name is given
        # then payload.result.NAME will be returned, otherwise a full copy of
        # the result is returned. Will raise ValueError() if the name is not
        # found.
    def get_result(self, name=None):
        if name is not None:
            if type(self.response_result) == dict:
                return self.response_result[name]
            else:
                raise ValueError('Result is not a dict')
        else:
            copy = getattr(self.response_result, 'copy', None)
            if callable(copy):
                return self.response_result.copy()
            else: 
                return self.response_result

# vim: set et cindent ts=4 ts=4 sw=4:
