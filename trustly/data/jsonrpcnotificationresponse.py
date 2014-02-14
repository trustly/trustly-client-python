import trustly.data.data

class JSONRPCNotificationResponse(trustly.data.data.Data):

    def __init__(self, request, success=None):
        super(JSONRPCNotificationResponse, self).__init__()

        uuid = request.get_uuid()
        method = request.get_method()

        if uuid is not None:
            self.set_result('uuid', uuid)

        if method is not None:
            self.set_result('method', method)

        if success is not None:
            self.set_success(success)

            # Static
        self.set('version', '1.1')

    def set_success(self, success=None):
        status = 'OK'
        if success is not None and success != True:
            status = 'FAILURE'

        self.set_data('status', status)

        return success

    def set_signature(self, signature):
        self.set_result('signature', signature)

    def set_result(self, name, value):
        if self.payload.get('result') is None:
            self.payload['result'] = dict()
        self.payload['result'][name] = value

    def get_result(self, name=None):
        result = self.payload.get('result')
        if result is None:
            if name is not None:
                raise KeyError('{0} is not present in the result'.format(name))
            else:
                return None

        if name is None:
            return result.copy()
        else:
            return result[name]

    def set_data(self, name, value):
        result = self.payload.get('result')
        if result is None:
            self.payload['result'] = dict(result=dict(data=dict()))

        data = result.get('data')
        if data is None:
            result['data'] = dict()
            data = result['data']

        data[name] = value
        return value


    def get_data(self, name=None):
        data = self.payload.get('result')
        if data is not None:
            data = data.get('data')
        if data is None:
            if name is not None:
                raise KeyError('{0} is not present in the result data'.format(name))
            else:
                return None

        if name is None:
            return data.copy()
        else:
            return data[name]

    def get_method(self):
        return self.get_result('method')

    def get_uuid(self):
        return self.get_result('uuid')
