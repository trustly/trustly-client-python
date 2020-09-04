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
import types

import trustly.data.request

class JSONRPCRequest(trustly.data.request.Request):
    payload = None

        # Initialize a new JSON RPC request data structure. Provide data and
        # attributes as needed for the call. If not provided they can later be
        # set using set_data() and set_attribute() calls. Data can be any type,
        # but if attributes are provided it MUST be a dict type otherwise a
        # TypeError will be issued.
        # method should be set to the name of the RPC method to call
    def __init__(self, method=None, data=None, attributes=None):
        super(JSONRPCRequest, self).__init__()

        payload = None
        if data is not None or attributes is not None:
                # Any data given we will store under params, so base from here
            payload = dict(params=dict())
                # Sanity check
            if data is not None:
                if type(data) != dict and attributes is not None:
                    raise TypeError('Data must be dict if attributes is provided')
                else:
                    payload['params']['Data'] = data
            else:
                    # We will need the data to add the attributes below
                payload['params']['Data'] = dict()

            if attributes is not None:
                payload['params']['Data']['Attributes'] = attributes

            self.payload = self.vacuum(payload)

            # We do not relay the method in the super call as for the JSON RPC
            # we keep this value in the payload and manage it ourself.
        if method is not None:
            self.payload['method'] = method

            # Initalize this to something useful, it will make life easier for
            # us later
        if self.payload.get('params') is None:
            self.payload['params'] = {}

        # Always send Attributes on Refund
        if method and method == 'Refund' and attributes is None:
            self.payload['params']['Data']['Attributes'] = None

            # Static
        self.set('version', '1.1')

        # Set a value in payload.params.NAME
    def set_param(self, name, value):
        self.payload['params'][name] = value

        # Fetch and clear value in payload.params.NAME
    def pop_param(self, name):
        return self.payload.get('params').pop(name, None)

        # Return a value from payload.params.NAME, will raise KeyError if name
        # is not present in params.
    def get_param(self, name):
        return self.payload['params'][name]

        # Set a new payload.params.UUID field value. Each call the trustly API
        # needs to have a unique UUID. 
    def set_uuid(self, uuid):
        return self.set_param('UUID', uuid)

        # Return the provided payload.params.UUID field, None if not set.
    def get_uuid(self):
        try:
            return self.get_param('UUID')
        except KeyError as e:
            return None
        except:
            raise

        # Set a new payload.method value. I.e. the RPC method to call
    def set_method(self, method):
        return self.set('method', method)

        # Return the method given in the call. None if not set.
    def get_method(self):
        try:
            return self.get('method')
        except KeyError as e:
            return None
        except:
            raise

        # Return a value from payload.params.Data, if the name field is not
        # given a complete copy of the Data structure will be returned. Raises
        # KeyError if the given name is not present in Data or Data is not yet
        # defined
    def get_data(self, name=None):
        data = self.get_param('Data')
        if data is None:
            raise KeyError(name)

        if name is None:
            try:
                return data.copy()
            except KeyError as e:
                return None
            except:
                raise
        else:
            return data[name]

        # Set a new value for payload.params.Data.name
    def set_data(self, name, value):
        if name is not None:
            if self.payload['params'].get('Data') is None:
                self.payload['params']['Data'] = {}

            self.payload['params']['Data'][name] = value

        return value

        # Return a new value for the payload.params.Data.Attributes field. If
        # name is not given returns a full copy of the Attributes structure.
        # Raises KeyError if the key is not present in the Attributes or if
        # Attributes or Data is not yet defined.
    def get_attribute(self, name=None):
        data = self.get_param('Data')
        if data is not None:
            attributes = data.get('Attributes')
        if attributes is None:
            raise KeyError(name)

        if name is None:
            try:
                return attributes.copy()
            except KeyError as e:
                return None
            except:
                raise
        else:
            return attrs[name]

        # Set a new payload.params.Data.Attributes.NAME value
    def set_attribute(self, name, value):
        if name is not None:
            if self.payload['params'].get('Data') is None:
                self.payload['params']['Data'] = {}

            if self.payload['params']['Data'].get('Attributes') is None:
                self.payload['params']['Data']['Attributes'] = {}

            self.payload['Data']['Attributes'][name] = value

        return value

# vim: set et cindent ts=4 ts=4 sw=4:
