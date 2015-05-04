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

import trustly.data.response
import trustly.exceptions

class JSONRPCResponse(trustly.data.response.Response):

        # Intialize a JSON RPC response from the result of a httplib call (not
        # yet read). The JSON Response from the call will be read and stored,
        # see trustly.data.Reponse for details on the response data stored. 
        # JSONRPCResponse additionally defines self.result wich will point to
        # the result structure for the call. 
    def __init__(self, call):
        super(JSONRPCResponse, self).__init__(call=call)

        version = self.get('version')

        if version != '1.1':
            raise trustly.exceptions.TrustlyJSONRPCVersionError('JSON RPC Version {0} is not supported'.format(version))

			# An unsigned JSON RPC Error result basically looks like this:
			# {
			#     "version": "1.1",
			#     "error": {
			#         "name": "JSONRPCError",
			#         "code": 620,
			#         "message": "ERROR_UNKNOWN"
			#     }
			# }
			#
			# And a unsigned result will be on the form:
			# {
			#     "version": "1.1",
			#     "result": {
			#         "now": "...",
			#         "data": []
			#     }
			# }
			#
			# We want response_result to always be the result of the
			# operation, The trustly.data will point response_result /result
			# or /error respectivly, we need to do nothing extra here
			#

        # Return the error code from the JSON RPC response, if any (None
        # otherwise). Will raise ValueError if the response was not an error.
    def get_error_code(self):
        if self.is_error():
            try:
                return self.response_result.get['code']
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
                return self.response_result.get['message']
            except KeyError as e:
                return None
            except:
                raise

        raise ValueError('The result is not an error')

# vim: set et cindent ts=4 ts=4 sw=4:
