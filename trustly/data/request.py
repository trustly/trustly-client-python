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

import trustly.data

class Request(trustly.data.data.Data):

    method = None

        # Initialize the data class using a full payload structure. Payload if
        # provided should be a dictionary formatted as the request should be. 
    def __init__(self, method=None, payload=None):
        super(Request, self).__init__(payload=payload)

        if method is not None:
            self.method = method
        elif payload is not None:
            self.method = self.payload.get('method')

        
        # Return the current method for which this call is destined
    def get_method(self):
        return self.method

        # Update method with a new value
    def set_method(self, method):
        self.method = method
        return method

        # Return the payload.uuid field if set, None otherwise.
    def get_uuid(self):
        return self.payload.get('uuid')

        # Set a new value for the payload.uuid field.
    def set_uuid(self, uuid):
        self.set('uuid', uuid)
        return uuid
 
# vim: set et cindent ts=4 ts=4 sw=4:
