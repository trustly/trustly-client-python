import trustly.data

class Request(trustly.data.data.Data):

    method = None

        # Initialize the data class using a full payload structure. Payload if
        # provided should be a dictionary formatted as the request should be. 
    def __init__(self, method=method, payload=None):
        super(Request, self).__init__(payload=payload)

        self.method = method
        
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
 

