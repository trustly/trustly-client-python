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
import six

class Data(object):
    payload = None

    def __init__(self):
        self.payload = {}

        # Vacuum out all keys being set to None in the data to be communicated
    def vacuum(self, data):
        if type(data) == list:
            ret = list()
            for k in data:
                if k is not None:
                    v = self.vacuum(k)
                    if v is not None:
                        ret.append(v)

            if len(ret) == 0:
                return None

            return ret

        elif type(data) == dict:
            ret = dict()
            for (k, v) in six.iteritems(data):
                if v is not None:
                    v = self.vacuum(v)
                    if v is not None:
                        ret[k] = v

            if len(ret) == 0:
                return None

            return ret
        else:
            return data


        # Fetch given key from the payload to be sent, will raise KeyError if
        # key is not present in the payload. Not providing key will return a
        # full copy of the payload.
    def get(self, name=None):
        if name is not None:
            return self.payload[name]
        else:
            return self.payload.copy()

        # Set a key in the payload to a given value
    def set(self, name, value):
        self.payload[name] = value
        return value

    def pop(self, name):
        return self.payload.pop(name, None)

        # Return a JSON representation (UTF-8) of the payoad
    def json(self, pretty=False):
        data = self.get()
        if pretty:
            return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))
        else:
            return json.dumps(data)

# vim: set et cindent ts=4 ts=4 sw=4:
