import json

import trustly.data

class JSONRPCNotificationRequest(trustly.data.data.Data):

    notification_body = None

    def __init__(self, notification_body):
        self.notification_body = notification_body
        try:
            payload = json.loads(self.notification_body)
        except ValueError as e:
            raise trustly.exceptions.TrustlyDataError(str(e))

        super(JSONRPCNotificationRequest, self).__init__(payload=payload)

        if self.get_version() != '1.1':
            raise trustly.exceptions.TrustlyJSONRPCVersionError('JSON RPC Version {0} is not supported'.format(self.get_version()))

    def get_params(self, name=None):
        params = self.payload.get('params')
        if name is None:
            if params is not None:
                return params.copy()
        elif params is not None:
            return params[name]
        else:
            raise KeyError('{0} is not present in params'.format(name))

        return None

    def get_data(self, name=None):
        params = self.payload.get('params')
        data = None
        if params is not None:
            data = params.get('data')

        if name is None:
            if data is not None:
                return data.copy()
        elif data is not None:
            return data[name]
        else:
            raise KeyError('{0} is not present in data'.format(name))

        return None

    def get_uuid(self):
        try:
            return self.get_params('uuid')
        except KeyError as e:
            pass

        return None

    def get_method(self):
        try:
            return self.get('method')
        except KeyError as e:
            pass

        return None

    def get_signature(self):
        try:
            return self.get_params('signature')
        except KeyError as e:
            pass

        return None

    def get_version(self):
        try:
            return self.get('version')
        except KeyError as e:
            pass

        return None
