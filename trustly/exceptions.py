class TrustlyJSONRPCVersionError(Exception):
    pass

class TrustlyConnectionError(Exception):
    pass

class TrustlyDataError(Exception):
    pass

class TrustlySignatureError(Exception):
    def __init__(self, message, data=None):
        super(TrustlySignatureError, self).__init__(message)
        self.signature_data = data

    def get_bad_data(self):
        return self.signature_data

class TrustlyAuthentificationError(Exception):
    pass
