import json
import types

class Data(object):
    payload = None

    def __init__(self, payload=None):
        if payload is not None:
            self.payload = self.vacuum(payload)

        if self.payload is None:
            self.payload = {}

        # Vacuum out all keys being set to None in the data to be communicated
    def vacuum(self, data):
        if type(data) == types.ListType:
            ret = list()
            for k in data:
                if k is not None:
                    v = self.vacuum(k)
                    if v is not None:
                        ret.append(v)

            if len(ret) == 0:
                return None

            return ret

        elif type(data) == types.DictType:
            ret = dict()
            for (k, v) in data.iteritems():
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
            return json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
        else:
            return json.dumps(data)
