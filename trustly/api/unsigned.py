import trustly.api.api
import trustly.data
import trustly.exceptions

class UnsignedAPI(trustly.api.api.API):
    api_username = None
    api_password = None
        # Session "password" will be used for authentification for all calls
        # after successful new_session_cookie call.
    session_uuid = None

    def __init__(self, username, password, host='trustly.com', port=443, is_https=True):

        super(UnsignedAPI, self).__init__(host=host, port=port, is_https=is_https)

        self.api_username = username
        self.api_password = password

    def url_path(self, request=None):
        return '/api/Legacy'

    def handle_response(self, request, httpcall):
        return trustly.data.jsonrpcresponse.JSONRPCResponse(httpcall)

    def insert_credentials(self, request):
        request.set_param('Username', self.api_username)
        if self.session_uuid is not None:
            request.set_param('Password', self.session_uuid)
        else:
            request.set_param('Password', self.api_password)

    def has_session_uuid(self):
        if self.session_uuid is not None:
            return True
        else:
            return False

    def new_session_cookie(self):
            # Unset the session password to force the add_credentials to send
            # the actual password rather then the session dito
        self.session_uuid = None

        data = trustly.data.jsonrpcrequest.JSONRPCRequest(method='NewSessionCookie')

            # Force call to super as we overload the call method to allow
            # arbitrary calls and will call new_session_cookie unless we have a
            # valid session cookie
        response = super(UnsignedAPI, self).call(data)

        if response.is_success():
            self.session_uuid = response.get_result('sessionuuid')
        else:
            raise trustly.exceptions.TrustlyAuthentificationError()

        return response

        # Execute the commonly used getviewstable
    def get_view_stable(self, viewname, dateorder=None, datestamp=None, filterkeys=None,
            limit=100, offset=0, params=None, sortby=None, sortorder=None):

        return self.call(method='GetViewStable',
                DateOrder=dateorder,
                Datestamp=datestamp,
                FilterKeys=filterkeys,
                Limit=limit,
                Offset=offset,
                Params=params,
                SortBy=sortby,
                SortOrder=sortorder,
                ViewName=viewname)

        # Execute an arbitrary call to the unsigned API. Retrieve new session
        # uuid unless we have already been given one
    def call(self, method, **kwargs):
        data = trustly.data.jsonrpcrequest.JSONRPCRequest(method=method)

        for (key, val) in kwargs.iteritems():
            data.set_param(key, val)

        if not self.has_session_uuid():
            self.new_session_cookie()

        return super(UnsignedAPI, self).call(data)

