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

            # We have errors in errors for the rpc responses. So go one step
            # further if possible
        if self.is_error():
            self.response_result = self.response_result.get('error')

        # Return the error code from the JSON RPC response, if any (None
        # otherwise). Will raise ValueError if the response was not an error.
    def get_error_code(self):
        if self.is_error():
            try:
                return self.result.get['error']['code']
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
                return self.result.get['error']['message']
            except KeyError as e:
                return None
            except:
                raise

        raise ValueError('The result is not an error')
