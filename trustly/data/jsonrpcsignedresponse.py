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

import types

import trustly.data.jsonrpcresponse
import trustly.exceptions

class JSONRPCSignedResponse(trustly.data.jsonrpcresponse.JSONRPCResponse):

        # Intialize a JSON RPC response from the result of a httplib call (not
        # yet read). The JSON Response from the call will be read and stored,
        # see trustly.data.Reponse for details on the response data stored. 
        # JSONRPCResponse additionally defines self.result wich will point to
        # the result structure for the call. 
    def __init__(self, call):
        super(JSONRPCSignedResponse, self).__init__(call=call)

        # A signed JSON RPC Error result basically looks like this:
        # {
        #     "version": "1.1",
        #     "error": {
        #             "error": {
        #                 "signature": "...",
        #                 "data": {
        #                 "code": 620,
        #                 "message": "ERROR_UNKNOWN"
        #             },
        #             "method": "...",
        #             "uuid": "..."
        #         },
        #         "name": "JSONRPCError",
        #         "code": 620,
        #         "message": "ERROR_UNKNOWN"
        #     }
        # }

        # A good signed result will be on the form:
        # {
        #     "version": "1.1",
        #     "result": {
        #         "signature": "...",
        #         "method": "...",
        #         "data": {
        #             "url": "...",
        #             "orderid": "..."
        #         },
        #         "uuid": "...",
        #     }
        # }
        # 
        # The trustly.data will point response_result /result or /error respectivly, we need to take care of the signed part here only.

        if self.is_error():
            self.response_result = self.response_result.get('error')

        # Return the error code from the JSON RPC response, if any (None
        # otherwise). Will raise ValueError if the response was not an error.
    def get_error_code(self):
        if self.is_error():
            try:
                return self.response_result['data']['code']
            except KeyError as e:
                return None
            except:
                raise

        raise ValueError('The result is not an error')

        # Return the error message from the JSON RPC response, if any (None
        # otherwise). Will raise ValueError if the response was not an error.
    def get_error_message(self):
        if self.is_error():
            try:
                return self.response_result['data']['message']
            except KeyError as e:
                return None
            except:
                raise

        raise ValueError('The result is not an error')

    def get_data(self, name=None):
        data = self.response_result.get('data')
        if data is None:
            if name is not None:
                raise KeyError('{0} is not present in the result data'.format(name))
            else:
                return None

        if name is None:
            return data.copy()
        else:
            return data[name]

# vim: set et cindent ts=4 ts=4 sw=4:
