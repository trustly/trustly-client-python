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

import httplib
import uuid
import base64
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA

import trustly.api.api
import trustly.exceptions
import trustly.data.jsonrpcrequest
import trustly.data.jsonrpcsignedresponse

class SignedAPI(trustly.api.api.API):
        # Basic key management, the actual key and the imported class
        # representation of the keys used in the integration. This is used for
        # communications with the parts of the API requiring signing of data
        # requests.
    merchant_privatekey = None
    merchant_signer = None

    api_username = None
    api_password = None

    def __init__(self, merchant_privatekey, username, password, host='trustly.com', port=443, is_https=True):

        super(SignedAPI, self).__init__(host=host, port=port, is_https=is_https)

        self.api_username = username
        self.api_password = password

        if merchant_privatekey is not None:
            if merchant_privatekey.find("\n") > -1:
                self.use_merchant_privatekey(merchant_privatekey)
            else:
                self.load_merchant_privatekey(merchant_privatekey)

    def load_merchant_privatekey(self, filename):
        pkeyfile = file(filename, 'r')
        cert = pkeyfile.read()
        pkeyfile.close()
        self.use_merchant_privatekey(cert)

    def use_merchant_privatekey(self, cert):
        self.merchant_privatekey = RSA.importKey(cert)
        self.merchant_signer = PKCS1_v1_5.new(self.merchant_privatekey)

    def sign_merchant_request(self, data):
        if self.merchant_signer is None:
            raise trustly.exceptions.TrustlySignatureError('No private key has been loaded for signing')

        method = data.get_method()
        if method is None:
            method = ''

        uuid = data.get_uuid()
        if uuid is None:
            uuid = ''

        data = data.get_data()
        if data is None:
            data = {}

        plaintext = unicode(method + uuid + self.serialize_data(data))
        sha1hash = SHA.new(plaintext.encode('utf-8'))
        signature = self.merchant_signer.sign(sha1hash)
        return base64.b64encode(signature)

    def insert_credentials(self, request):
        request.set_data('Username', self.api_username)
        request.set_data('Password', self.api_password)
        request.set_param('Signature', self.sign_merchant_request(request))

    def handle_response(self, request, httpcall):
        response = trustly.data.jsonrpcsignedresponse.JSONRPCSignedResponse(httpcall)

        if not self.verify_trustly_signed_response(response):
            raise trustly.exceptions.TrustlySignatureError('Incoming message signature is not valid', response)

        if response.get_uuid() != request.get_uuid():
            raise trustly.exceptions.TrustlyDataError('Incoming response is not related to request. UUID mismatch.')

        return response

    def notification_response(self, notification, success=True):
        response = super(SignedAPI, self).notification_response(notification, success)

        signature = self.sign_merchant_request(response)
        response.set_signature(signature)
        return response

    def url_path(self, request=None):
        return '/api/1'

    def call(self, request):
        if request.get_uuid() is None:
            request.set_uuid(str(uuid.uuid1()))

        return super(SignedAPI, self).call(request)

    def deposit(self, notificationurl, enduserid, messageid, 
            locale=None, amount=None, currency=None, country=None, ip=None,
            successurl=None, failurl=None, templateurl=None, urltarget=None,
            mobilephone=None, firstname=None, lastname=None,
            nationalidentificationnumber=None, shopperstatement=None,
            suggestedminamount=None, suggestedmaxamount=None,
            integrationmodule=None, holdnotifications=None):

        attributes = dict(
                Locale=locale,
                Amount=amount,
                Currency=currency,
                Country=country,
                IP=ip,
                SuccessURL=successurl,
                FailURL=failurl,
                TemplateURL=templateurl,
                URLTarget=urltarget,
                MobilePhone=mobilephone,
                Firstname=firstname,
                Lastname=lastname,
                NationalIdentificationNumber=nationalidentificationnumber,
                ShopperStatement=shopperstatement,
                SuggestedMinAmount=suggestedminamount,
                SuggestedMaxAmount=suggestedmaxamount,
                IntegrationModule=integrationmodule
                )

        if holdnotifications:
            attributes['HoldNotifications'] = 1

        data = trustly.data.jsonrpcrequest.JSONRPCRequest(method='Deposit',
                data=dict(
                    NotificationURL=notificationurl,
                    EndUserID=enduserid,
                    MessageID=messageid
                    ),
                attributes=attributes
                )
        return self.call(data)

    def withdraw(self, notificationurl,
            enduserid, messageid, currency,
            locale=None, country=None, ip=None, templateurl=None,
            clearinghouse=None, banknumber=None, accountnumber=None,
            firstname=None, lastname=None, mobilephone=None,
            nationalidentificationnumber=None, address=None,
            holdnotifications=None):

        attributes = dict(
                Locale=locale,
                Country=country,
                IP=ip,
                TemplateURL=templateurl,
                ClearingHouse=clearinghouse,
                BankNumber=banknumber,
                AccountNumber=accountnumber,
                Firstname=firstname,
                Lastname=lastname,
                MobilePhone=mobilephone,
                NationalIdentificationNumber=nationalidentificationnumber,
                Address=address
                )

        if holdnotifications:
            attributes['HoldNotifications'] = 1

        data = trustly.data.jsonrpcrequest.JSONRPCRequest(method='Withdraw',
                data=dict(
                    NotificationURL=notificationurl,
                    EndUserID=enduserid,
                    MessageID=messageid,
                    Currency=currency,
                    Amount=None
                    ),
                attributes=attributes
                )
        return self.call(data)

    def refund(self, orderid, amount, currency):

        data = trustly.data.jsonrpcrequest.JSONRPCRequest(method='Refund',
                data=dict(
                    OrderID=orderid,
                    Amount=amount,
                    Currency=currency
                    )
                )

        return self.call(data)

    def denywithdrawal(self, orderid):

        data = trustly.data.jsonrpcrequest.JSONRPCRequest(method='DenyWithdrawal',
                data=dict(
                    OrderID=orderid
                    )
                )

        return self.call(data)

    def approvewithdrawal(self, orderid):

        data = trustly.data.jsonrpcrequest.JSONRPCRequest(method='ApproveWithdrawal',
                data=dict(
                    OrderID=orderid
                    )
                )

        return self.call(data)

    def selectaccount(self, notificationurl, enduserid, messageid,
            locale=None, country=None, ip=None, successurl=None, urltarget=None,
            mobilephone=None, firstname=None, lastname=None, 
            holdnotifications=None):

        attributes = dict(
            Locale=locale,
            Country=country,
            IP=ip,
            SuccessURL=successurl,
            URLTarget=urltarget,
            MobilePhone=mobilephone,
            Firstname=firstname,
            Lastname=lastname
        )

        if holdnotifications:
            attributes['HoldNotifications'] = 1

        data = trustly.data.jsonrpcrequest.JSONRPCRequest(method='SelectAccount',
                data=dict(
                    NotificationURL=notificationurl,
                    EndUserID=enduserid,
                    MessageID=messageid
                    ),
                attributes=attributes
                )
        return self.call(data)

    def registeraccount(self, enduserid, clearinghouse, banknumber,
            accountnumber, firstname, lastname, mobilephone=None,
            nationalidentificationnumber=None, address=None,
            holdnotifications=None):

        attributes = dict(
            MobilePhone=mobilephone,
            NationalIdentificationNumber=nationalidentificationnumber,
            Address=address
        )

        if holdnotifications:
            attributes['HoldNotifications'] = 1

        data = trustly.data.jsonrpcrequest.JSONRPCRequest(method='RegisterAccount',
                data=dict(
                    EndUserID=enduserid,
                    ClearingHouse=clearinghouse,
                    BankNumber=banknumber,
                    AccountNumber=accountnumber,
                    Firstname=firstname,
                    Lastname=lastname
                    ),
                attributes=attributes
                )
        return self.call(data)

    def accountpayout(self, notificationurl, accountid, enduserid, messageid,
            amount, currency):

        data = trustly.data.jsonrpcrequest.JSONRPCRequest(method='AccountPayout',
                data=dict(
                    NotificationURL=notificationurl,
                    AccountID=accountid,
                    EndUserID=enduserid,
                    MessageID=messageid,
                    Amount=amount,
                    Currency=currency
                    ),
                attributes=dict(
                    )
                )
        return self.call(data)

    def p2p(self, notificationurl, enduserid, messageid,
            locale=None, amount=None, currency=None, country=None, ip=None,
            successurl=None, failurl=None, templateurl=None, urltarget=None,
            mobilephone=None, firstname=None, lastname=None,
            nationalidentificationnumber=None, shopperstatement=None,
            suggestedminamount=None, suggestedmaxamount=None,
            integrationmodule=None, holdnotifications=None,
            authorizeonly=None, templatedata=None):

        attributes = dict(
                AuthorizeOnly=self.api_bool(authorizeonly),
                TemplateData=templatedata,
                Locale=locale,
                Amount=amount,
                Currency=currency,
                Country=country,
                IP=ip,
                SuccessURL=successurl,
                FailURL=failurl,
                TemplateURL=templateurl,
                URLTarget=urltarget,
                MobilePhone=mobilephone,
                Firstname=firstname,
                Lastname=lastname,
                NationalIdentificationNumber=nationalidentificationnumber,
                ShopperStatement=shopperstatement,
                SuggestedMinAmount=suggestedminamount,
                SuggestedMaxAmount=suggestedmaxamount,
                IntegrationModule=integrationmodule
                )

        if holdnotifications:
            attributes['HoldNotifications'] = 1

        data = trustly.data.jsonrpcrequest.JSONRPCRequest(method='P2P',
                data=dict(
                    NotificationURL=notificationurl,
                    EndUserID=enduserid,
                    MessageID=messageid
                    ),
                attributes=attributes
                )
        return self.call(data)

    def capture(self, orderid, amount, currency):

        data = trustly.data.jsonrpcrequest.JSONRPCRequest(method='Capture',
                data=dict(
                    OrderID=orderid,
                    Amount=amount,
                    Currency=currency
                    ),

                attributes=dict(
                    )
                )
        return self.call(data)

    def void(self, orderid):

        data = trustly.data.jsonrpcrequest.JSONRPCRequest(method='Void',
                data=dict(
                    OrderID=orderid
                    ),

                attributes=dict(
                    )
                )
        return self.call(data)


    def hello(self):
            # The hello call is not signed, use an unsigned API to do the request and then void it 
        api = trustly.api.unsigned.UnsignedAPI(username=self.api_username, password=self.api_password,
                host=self.api_host, port=self.api_port, is_https=self.api_is_https)

        return api.hello()

# vim: set et cindent ts=4 ts=4 sw=4:
