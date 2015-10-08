#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import pprint
import tempfile
import time
import uuid
import json

import trustly.api.api
import trustly.api.signed
import trustly.data.jsonrpcsignedresponse
import trustly.data.jsonrpcnotificationrequest
import trustly.exceptions


mock_api_response_code = None
mock_api_response_reason = None
mock_api_response_body = None
# These are set by MockHTTPCall.request and cleared by mock_api_connect
mock_api_input_method = None
mock_api_input_body = None
mock_api_input_url = None

class MockResponse(object):
    reason = None
    status = None
    body = None

    def __init__(self, reason, status, body):
        self.reason = reason
        self.status = status
        self.body = body

    def read(self):
        return self.body

class MockHTTPCall(object):
    status = None
    reason = None
    body = None

    def __init__(self, status, reason, body):
        self.status = status
        self.reason = reason
        self.body = body

    def getresponse(self):
        return MockResponse(
                reason=self.reason,
                status=self.status,
                body=self.body
                )

    def request(self, method, url, body):
        global mock_api_input_method
        global mock_api_input_url
        global mock_api_input_body

        mock_api_input_method = method
        mock_api_input_url = url
        mock_api_input_body = body


def mock_api_connect():
    global mock_api_response_code
    global mock_api_response_reason
    global mock_api_response_body
    global mock_api_input_method
    global mock_api_input_url
    global mock_api_input_body

    mock_api_input_method = None
    mock_api_input_url = None
    mock_api_input_body = None

    return MockHTTPCall(status=mock_api_response_code,
            reason=mock_api_response_reason,
            body=mock_api_response_body)

mock_uuid1 = None
def mock_uuid_uuid1():
    global mock_uuid1
    return mock_uuid1

class APITestCase(unittest.TestCase):
    api = None
    def setUp(self):
        self.api = trustly.api.api.API(host='test.trustly.com', port=443, is_https=True)

    def tearDown(self):
        pass

    def testCreate(self):
        self.assertIsNotNone(self.api, msg="Create test.trustly.com API instance")

        # Test loading a bogus host key just to make sure we blow up and also
        # preserves the proper internals.
        with self.assertRaises(IOError, msg='Set host without known publickey'):
            self.api.set_host(host='foobar.trustly.com')

        self.assertEqual(self.api.api_host, 'test.trustly.com', msg='Host information not changed when setting bad host')


    # serialize data
    def testSerialize(self):
        # example from https://trustly.com/en/developer/api#/signature

        ex1 = {
                'MyKey': 'MyValue',
                'MyArray': [
                    'Element1',
                    'Element2',
                    {
                        'mykey2': 'myvalue2'
                        }
                    ]
                }

        self.assertEqual(self.api.serialize_data(ex1),
                'MyArrayElement1Element2mykey2myvalue2MyKeyMyValue',
                msg='Serialize homepage example')
        ex2 = {
            'params': {
                'Data': {
                    'MessageID': '71b98590-ea13471f-13d68d13',
                    'EndUserID': 'd2819cbe',
                    'NotificationURL': 'http://dev1:1080/sinkhole',
                    'Attributes': {
                        'Currency': 'SEK',
                        'Amount': '12.47',
                        'SuccessURL': 'http://dev1:1080/success.html',
                        'Firstname': 'Eduardo',
                        'FailURL': 'http://dev1:1080/failure.html',
                        'Locale': 'sv_SE',
                        'Lastname': 'Chavez',
                        'URLTarget': '0'
                    },
                    'Password': 'testuser',
                    'Username': 'testuser'
                },
                'UUID': 'e07c7d6a-6b40-11e5-9d5e-0800279bcb51',
                'Signature': 'fPGxJQRMXAy...=='
            },
            'method': 'P2P',
            'version': '1.1'
        }

        self.assertEqual(self.api.serialize_data(ex2),
            'methodP2PparamsDataAttributesAmount12.47CurrencySEKFailURLhttp://dev1:1080/failure.htmlFirstnameEduardoLastnameChavezLocalesv_SESuccessURLhttp://dev1:1080/success.htmlURLTarget0EndUserIDd2819cbeMessageID71b98590-ea13471f-13d68d13NotificationURLhttp://dev1:1080/sinkholePasswordtestuserUsernametestuserSignaturefPGxJQRMXAy...==UUIDe07c7d6a-6b40-11e5-9d5e-0800279bcb51version1.1',
            msg='Serialize ex2')

        ex3 = {
                'nullvalue': None,
                'array': [
                    '012',
                    '013',
                    '011',
                    '014',
                    'abc',
                    '010',
                    'def'
                    ],
                'deep1': {
                    'deep2': {
                        'deep3': {
                            'deep4': {
                                'deep5': {
                                    }
                                }
                            }
                        },
                    },
                'arrayofarray1': [
                    [
                        [
                            [
                                [
                                    [
                                        9,
                                        5,
                                        1,
                                        10
                                        ]
                                    ]
                                ]
                            ]
                        ],
                    [
                        'abc',
                        'foo',
                        '01',
                        ]
                    ]
                }

        self.assertEqual(self.api.serialize_data(ex3),
            'array012013011014abc010defarrayofarray195110abcfoo01deep1deep2deep3deep4deep5nullvalue',
            msg='Serialize ex3')

        ex4 = 'scalar'

        self.assertEqual(self.api.serialize_data(ex4),
            'scalar',
            msg='Serialize ex4')

        ex5 = [
                'feg',
                'abc',
                '123'
                ]

        self.assertEqual(self.api.serialize_data(ex5),
            'fegabc123',
            msg='Serialize ex5')

        ex6 = {
                u'öäå': 3,
                u'äåö': 2,
                u'åöä': 1,
                }

        self.assertEqual(self.api.serialize_data(ex6),
            u'äåö2åöä1öäå3',
            msg='Serialize ex6')



    def testSignedResponse(self):
        response1body = """{
    "result": {
        "data": {
            "orderid": "1371798227",
            "url": "https://test.trustly.com/_/orderclient.php?SessionID=11139ac4-f0c1-4594-8211-7f4c10e61212&OrderID=1371798227&Locale=sv_SE"
        },
        "method": "Deposit",
        "signature": "mB/GNR5LmDGPsCDXgoaZOmEN3KKj0Q/UwpmUf4WwHht2Y0ISPJ/r9htgegWjCCvkNrTUZNHcSZCn3fPaiF9h0QY1zoTbrgCeYE7SLqPoPY5ineKCYvE4xwnJRc41QRqeYwkQmDRz6tN1vi2iKetcRBH4vtILgldO0LdR4dyjiI6w2MNSQiZCwZnO2kr81KD3Kaqr9NxPyt1LI+VxkXwdcUhWcVFfLvUZZWWZLZS4vlQR5/XjDRo7ngGqEC6fceAjZE1NPptmXrFuafvkvWIRdTleEioNPyV4yua9pAyRnDurzfG0T0A73vAgfmWCBddhz/aAGxNLWR9PWofSawGj9g==",
        "uuid": "a4d1578e-6c00-11e5-9d5e-0800279bcb51"
    },
    "version": "1.1"
}
"""
        mockhttpcall1 = MockHTTPCall(200, None, response1body)
        response1 = trustly.data.jsonrpcsignedresponse.JSONRPCSignedResponse(call=mockhttpcall1)
        ok = self.api.verify_trustly_signed_response(response1)
        self.assertEqual(ok, True, msg='Response verified OK')

        # Modified the orderid, kept the signature
        response2body = """{
    "result": {
        "data": {
            "orderid": "1371798228",
            "url": "https://test.trustly.com/_/orderclient.php?SessionID=11139ac4-f0c1-4594-8211-7f4c10e61212&OrderID=1371798227&Locale=sv_SE"
        },
        "method": "Deposit",
        "signature": "mB/GNR5LmDGPsCDXgoaZOmEN3KKj0Q/UwpmUf4WwHht2Y0ISPJ/r9htgegWjCCvkNrTUZNHcSZCn3fPaiF9h0QY1zoTbrgCeYE7SLqPoPY5ineKCYvE4xwnJRc41QRqeYwkQmDRz6tN1vi2iKetcRBH4vtILgldO0LdR4dyjiI6w2MNSQiZCwZnO2kr81KD3Kaqr9NxPyt1LI+VxkXwdcUhWcVFfLvUZZWWZLZS4vlQR5/XjDRo7ngGqEC6fceAjZE1NPptmXrFuafvkvWIRdTleEioNPyV4yua9pAyRnDurzfG0T0A73vAgfmWCBddhz/aAGxNLWR9PWofSawGj9g==",
        "uuid": "a4d1578e-6c00-11e5-9d5e-0800279bcb51"
    },
    "version": "1.1"
}
"""
        mockhttpcall2 = MockHTTPCall(200, None, response2body)
        response2 = trustly.data.jsonrpcsignedresponse.JSONRPCSignedResponse(call=mockhttpcall2)
        ok = self.api.verify_trustly_signed_response(response2)
        self.assertEqual(ok, False, msg='Response verified NOT OK')

    def testSignedNotification(self):
        notification1 = """{
    "method": "credit",
    "params": {
        "data": {
            "currency": "SEK",
            "enduserid": "leecS",
            "messageid": "5001_655548",
            "timestamp": "2015-03-12 15:14:18.61671+00",
            "notificationid": "3653956920",
            "amount": "20.00",
            "orderid": "3931155141"
        },
        "signature": "jzsoXu5OtwfMe20l5AXGk0sdQsxo8/xe+RKtSEMfdQ9RjqDW6tF+xHdsyTH04xwU1aVXOqBVOnOaIZX6PbgASEhG1GDxq2tY533ptBn9P6dAp8njWBvp2qidb8tNd2Z+Gwx8hyTBcNWtL/AxO5gZOwlJvgNwtpWFaDW7ejYcVZ+V/tsPk93odzo40lGZqJsZar7927s1Z2ewkrCl9sM39obZqSswsF41THC0uDL5CAXDoRafrQC63KbF4zMV7HaudNJcnzQIGCr/+yGLEZoARHJZHNb0fIlVMCroKk+rsHg9P3/QglAJD34U2SrQW5CM+qgVWgcoscJHEhAlmwyoTQ==",
        "uuid": "f1b77aac-516d-4b89-a125-c005f4c020f0"
    },
    "version": "1.1"
}
"""
        response1 = self.api.handle_notification(notification1)
        self.assertEqual(response1.get_method(), 'credit', msg='Notification parsed and can return method')

        # Modified the messageid, kept the signature
        notification2 = """{
    "method": "credit",
    "params": {
        "data": {
            "currency": "SEK",
            "enduserid": "leecS",
            "messageid": "5001_655549",
            "timestamp": "2015-03-12 15:14:18.61671+00",
            "notificationid": "3653956920",
            "amount": "20.00",
            "orderid": "3931155141"
        },
        "signature": "jzsoXu5OtwfMe20l5AXGk0sdQsxo8/xe+RKtSEMfdQ9RjqDW6tF+xHdsyTH04xwU1aVXOqBVOnOaIZX6PbgASEhG1GDxq2tY533ptBn9P6dAp8njWBvp2qidb8tNd2Z+Gwx8hyTBcNWtL/AxO5gZOwlJvgNwtpWFaDW7ejYcVZ+V/tsPk93odzo40lGZqJsZar7927s1Z2ewkrCl9sM39obZqSswsF41THC0uDL5CAXDoRafrQC63KbF4zMV7HaudNJcnzQIGCr/+yGLEZoARHJZHNb0fIlVMCroKk+rsHg9P3/QglAJD34U2SrQW5CM+qgVWgcoscJHEhAlmwyoTQ==",
        "uuid": "f1b77aac-516d-4b89-a125-c005f4c020f0"
    },
    "version": "1.1"
}
"""
        with self.assertRaises(trustly.exceptions.TrustlySignatureError, msg='Bad notification raises exception'):
            self.api.handle_notification(notification2)

    def testBaseURL(self):
        self.api.set_host(host='test.trustly.com', port=443, is_https=True)
        self.assertEqual(self.api.base_url(), 'https://test.trustly.com', msg='API URL test/443/is_https')
        self.api.set_host(host='test.trustly.com', port=80, is_https=True)
        self.assertEqual(self.api.base_url(), 'https://test.trustly.com:80', msg='API URL test/80/is_https')
        self.api.set_host(host='test.trustly.com', port=80, is_https=False)
        self.assertEqual(self.api.base_url(), 'http://test.trustly.com', msg='API URL test/80')
        self.api.set_host(host='test.trustly.com', port=443, is_https=False)
        self.assertEqual(self.api.base_url(), 'http://test.trustly.com:443', msg='API URL test/443')


class SignedAPITestCase(unittest.TestCase):
    api = None
    old_api_connect = None
    old_uuid_uuid1 = None

    def setUp(self):
        self.privatekey1 = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAuw7IsyA8ZrdmdOootjklO7LqERnthF0Yctd1waykOnMexePQ
luyIzedkfOHzFXb9FjBNJ+VQ2Obpw94P+tszyvGpauAywpJYV4h4IldSCiablshB
5AefmRuEQci3iTP0vNTQ71Rs4V3+XbkXpLtv4XSqx1mZ0OBUm66Eq9IYLIzSnpv5
uXU2Xk1wgsIUxm0v8AFeSx9RlISc3aAEfucjSve9dqQ9evwH5SQZTdD8zhZmzrgc
EC8u3swLaQ5Xou3X335CBknVZOsqAaVkvWy0K5f7SJ6btCUwnjq9w4jfY5RSN90x
q7yk/D6I99pIbrrqBLR05ZJTAREkGqAM7+efdQIDAQABAoIBAF7KuCQl8tXunKok
u2rUfKzLFtiBth58etY/n3n8/eBs1CxeLSc+SHlniEHM0r2O5eQnqAHOsHCqW84Z
KynpiU6PtlXltXNqbAA3tQFaFMX2GKSJaPKgdl1FV3lquK97t8s1YYfW1bJDSpK+
KGAfaCvtTlnlaxAxjk6yWqMjvYJdIGje29p+maCTs/4Gzv7hQEdsDi8L5Udswd6t
dscLCOtwKz7p7Bte51wrblGgxvT+UwP8diZ0b6/cJhYIkKyMlhNMb+s6ZvFhXRbO
IMcJmKHcPIuvzfQNTJnYNepRa4Xaq6bC6ybKhEEaeKxoweC/tecMv01r8NHlDPcu
0S+bzeECgYEA6QBtN5dfJvPCmRDO8SqgJZz+Mu90gEIYyMwr5mf4I4P/Oxq50Dvt
U3+11Ph3oVBHZ06VDUstsV/31/r2NU2mXeDLniw416eF/VSrZQtDswikMaKvE/Iq
ZRWG6H/t6qtv1EM5mbwfJzkc1nYu4wdcwKrtjTFj6agO9mlk9lZbbJkCgYEAzYVt
5C+Go4uGCPEvL75st2C8/wLxuUUGH3ma/Keikly0HbIjrRGWDn15eJRo6nlppj5t
hMq0l1q9blfV3kKlcYg3qwPxaqzP9C4qctlK0sCSiWpk5kUqQ++1tUFUKgsLMIPL
AbQj/it7GYlUBzRfeYDaXaWmODdg1GPVY9VlFz0CgYBeUG3lMsCxY7pBeyxJMpfg
ocvDkmn2AMtHfF3Ixg0LU0LdCdRtFdTbF7binjDOe1Br4MM0vlmgktgf9NX0fZn6
JiRFwmC/6m+yO7OlEwo0TisobFGyITRH9o7FTgNgGkUKBqwqLpvtpJCnvu77tt80
nfvKS1PGIODtnXvgutQHAQKBgBj/KI1/Zk3P83507ztMWua24mXV0tao2YTMgphG
P1Sz58hQ2Vv8bpbWlgafbl9OYxYwM5vaF7rs82tPTZjZ3EuBuNuZACzsVeKqFsmf
OiWF/IywHxOOyAQ5TI1+I6F1dGfzL6bGZTZNzYwektTJfu9FR8nqEtx1h9ZtSg/5
bXE1AoGBALlSRbcEez/HJaAk36LC5hULylM8lEzkOID8vhi2/VTVaAEg3tlbho/X
Uqnv5ngF2T5WC3BfY9IZRZw9YaEDSwrHddjzl08/mLBceQUZQkjmH38oB+2SRGyA
UNiBeE+cfYCIgQlRRMaA6f5UyGN76CMNhq1/em9oSb+8orFP0B72
-----END RSA PRIVATE KEY-----"""
        self.privatekey2 = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA7RW38DxmnFPwirOn9cgXSUqWGfGC5WLuVTTPKgJ5IkQb2Pij
NiVAEkg5v4ANk1p2yzI8z0g1j1TLWIKp30yyHeyivcWRL4HhGXehWovTgcNXMed7
3bNswnt7HsZOvSWmpY49NBfPfbKedT+MJW8X3FmU7UQqDxxRslf1SkMSQ8YL4YkU
EuOeLXfLVTF/pZgihaHdVAV+B+/evKq1PtTZcNVIfiCf7tqs+G6k7pjCefnzkvJr
Wo7z4cFWft6rWjmhCPwYYA2VogT8xbgjwIQFDN6FGGZu264o8v4nNcFZcurKw4zg
BXM16ikZSEEhgMzzAlYq6ORaD7MYIzqC2iLZJQIDAQABAoIBADDqtEL7E2jZ4N2d
Z+BMYpGatBGyRQGzQd2Owde3Hus1BlHkKzi2wtuCz3d1oldu6OfP+8AA9BwYsMQY
YZhTKMUH2CQzqVsV/y3UAxS9mOxDM7B2RJZfuOb/t02IOSLJq/KowHQJHaSfwBYN
AIuQummaiiHSWKM5gpm7kD68S/5zbsIs5hC9FL71SxgzRxbbOrPyEBfukMJjlZsI
dZTM/oVOOKP25R7SexFokcWfi2G/un2/nggdMahL6T4VOc01Yo5OAO4+IYkF0un6
KWH6XfgA+AAeJxa7al6zoEm1Tz603wRhpWSoyJp8SK6IgZoKGJ7FVPPheqtdf/J9
UrMpJgECgYEA92M+kfLaXXRyEEhHc867DMKpFcL54fN6s23Pgh19TOl3d5kb2xiC
3mHAra21JDNurP4IFH253tm4wErbAsblUPKg9LDL2cxKigUD0SiHIj7ClxZsTLlu
1h/3Y05UPMWhlWBYrQazoTTcgU5QVrBswSF1qPl/sp+pZUO6lyCy2WUCgYEA9Van
WMjGeFgz7IxvE6MFfpXcayPezaBIpBVNKM6sal6cSwDR2900N3l+PAyS32pXszlb
jreqEp4irxSAnNRR2ysiBEpdy5o3x6+bdTygTxb638m+7cA1FE7rEVlUVK2CziVb
7Ev871TEOPWjsrjUdp+Zl9XnAplE0VqcLs+D5MECgYEAmMH7nPuswxBobo1zMZtx
/QsmhX2D93X1Sl6ASAQVnyx6zKsKfFvCU7dg1t3wgI4RxViHfL+1yln+rx6J5kkS
yM1Jfk69UZvIWzmFhd3Us9y1I76A2U+XlTjf9b4kXfJbOHXpy83blauijWXiTeVb
Ala65MBLjezxGMqdqTxTs9ECgYEA39bp5FV6zz4aUc5nYdExKCdu7cnSdGWzIRHW
Tk8SfBJKIxxiXGlcROjyRbNrJbAOyBSi9nmYEFh7aKYaGfyVmpOl+6gmH6dbETOl
cLeZw89BoYCeVKkzRI4kZrXL/V45o//t+I/z/CCozxc+/ccpAfnn1uJwXKyeXyx+
py7qNYECgYBZofTxhBGSrqcqg+AknZTOsoDw8S+rdsLVBsAiAJQwOFKmR5a/KfFj
JYecd5ulTmPnGgc4ldSIK+9KOndsPt4TVBhIwML7SUxLIk+Z7AQChnNcLKm+eRy4
cUFIRR0bMucePoXoCZEPx93iOTUgBruJ+N3eNHTr+1TX/EvNW1mkcg==
-----END RSA PRIVATE KEY-----"""
        self.api = trustly.api.signed.SignedAPI(merchant_privatekey=self.privatekey1,
                username='testusername',
                password='testpassword',
                host='test.trustly.com',
                port=443,
                is_https=True)

    def tearDown(self):
        pass

    def testCreate(self):
        self.assertIsNotNone(self.api, msg='API Created with text privatekey1')
        self.assertEqual(self.api.merchant_privatekey.exportKey(format='PEM'), self.privatekey1,
                msg='API created with privatekey1 string')

        privatekeyfile = tempfile.NamedTemporaryFile()
        privatekeyfile.write(self.privatekey2)
        privatekeyfile.flush()

        api2 = trustly.api.signed.SignedAPI(merchant_privatekey=privatekeyfile.name,
                username='testusername',
                password='testpassword',
                host='test.trustly.com',
                port=443,
                is_https=True)
        self.assertEqual(api2.merchant_privatekey.exportKey(format='PEM'), self.privatekey2,
                msg='API created from file based private key')
        privatekeyfile.close()

        api2.use_merchant_privatekey(self.privatekey1)
        self.assertEqual(api2.merchant_privatekey.exportKey(format='PEM'), self.privatekey1,
                msg='API can switch privatekey')


        # Monkeypatch strategic calls so we can hook in responses and capture the request
    def _setup_mock_call(self, response_body=None, response_code=200, response_reason=None, call_uuid=None):
        global mock_api_response_code
        global mock_api_response_reason
        global mock_api_response_body
        global mock_uuid1

        if self.old_api_connect is None:
            self.old_api_connect = self.api.connect
            self.api.connect = mock_api_connect

        if self.old_uuid_uuid1 is None:
            self.old_uuid_uuid1 = uuid.uuid1
            uuid.uuid1 = mock_uuid_uuid1

        mock_api_response_body = response_body
        mock_api_response_code = response_code
        mock_api_response_reason = response_reason
        mock_uuid1 = call_uuid

    def _teardown_mock_call(self):
        if self.old_api_connect is not None:
            self.api.connect = self.old_api_connect
        if self.old_uuid_uuid1 is not None:
            uuid.uuid1 = self.old_uuid_uuid1

        self.old_api_connect = None
        self.old_uuid_uuid1 = None

    def testDeposit(self):
        global mock_api_input_method
        global mock_api_input_url
        global mock_api_input_body

        self._setup_mock_call(
                response_body = """{"version":"1.1","error":{"error":{"uuid":"ad4f3dbe-6c1d-11e5-9d5e-0800279bcb51","signature":"bsu/qaPV6nQoyXvB6Ljlr5sWCntjBGcz9sgxawGtRHakMU3JZnJ7Iv/zR3S3BbcIhB8uSNybNlAgmXtOnrpdZ7HtN5CIKEh60h8mxvbq3asBuLbMqN9Bpeala9NgiBQiH9uq7tcY8xOSVbUJLcXWonn6QVBZGL4LJwcAXQOLfen/YBOETS0mcsXn8vpAKZeQf6IH4RwYUHlzisRjsW+8fKMJm9DchwmmEnrY4n34ucudMTPRISwRiSWjAupH+3ls5JEsfjAsSaHSeQw7O/kTRLetEP4Zs8I/bc1oQeE7S4djd6jwRKlwZp3dvZmUVPHKxYcOQrQXfIWMBIztayFhUw==","data":{"message":"ERROR_INVALID_CREDENTIALS","code":616},"method":"Deposit"},"name":"JSONRPCError","code":616,"message":"ERROR_INVALID_CREDENTIALS"}}""",
                call_uuid="ad4f3dbe-6c1d-11e5-9d5e-0800279bcb51"
                )

        response = self.api.deposit(
                notificationurl='http://notificationurl',
                enduserid='enduser01',
                messageid='message01',
                locale='en_US',
                amount='12.34',
                currency='SEK',
                country='SE',
                ip='127.0.0.1',
                successurl='http://successurl',
                failurl='http://failurl',
                templateurl='http://templateurl',
                urltarget='urltarget01',
                mobilephone='mobilephone01',
                firstname='firstname01',
                lastname='lastname01',
                nationalidentificationnumber='nationalidentificationnumber01',
                shopperstatement='shopperstatement01',
                suggestedminamount='10.01',
                suggestedmaxamount='100.01',
                integrationmodule='integrationmodule01',
                holdnotifications=True
                );

        self.assertEqual(response.is_success(), False, msg='Bad deposit call is not a success')
        self.assertEqual(response.is_error(), True, msg='Bad deposit call is an error')
        self.assertEqual(response.get_error_code(), 616, msg='Bad deposit call result is 616 error')
        self.assertEqual(response.get_error_message(), 'ERROR_INVALID_CREDENTIALS', msg='Bad deposit call result is ERROR_INVALID_CREDENTIALS error')
        self.assertEqual(response.get_method(), 'Deposit', msg='Bad deposit call result is from Deposit')

        request = json.loads(mock_api_input_body)
        facit = {
                "version": "1.1",
                "params": {
                    "Data": {
                        "Username": "testusername",
                        "NotificationURL": "http://notificationurl",
                        "MessageID": "message01",
                        "Attributes": {
                            "Country": "SE",
                            "SuggestedMaxAmount": "100.01",
                            "Amount": "12.34",
                            "FailURL": "http://failurl",
                            "SuggestedMinAmount": "10.01",
                            "HoldNotifications": 1,
                            "MobilePhone": "mobilephone01",
                            "Firstname": "firstname01",
                            "Currency": "SEK",
                            "Locale": "en_US",
                            "Lastname": "lastname01",
                            "ShopperStatement": "shopperstatement01",
                            "URLTarget": "urltarget01",
                            "SuccessURL": "http://successurl",
                            "IP": "127.0.0.1",
                            "TemplateURL": "http://templateurl",
                            "IntegrationModule": "integrationmodule01",
                            "NationalIdentificationNumber": "nationalidentificationnumber01"
                            },
                        "Password": "testpassword",
                        "EndUserID": "enduser01"
                        },
                    "UUID": "ad4f3dbe-6c1d-11e5-9d5e-0800279bcb51",
                    "Signature": "GYDWKq4dpx7gF4YMck7IMT/lL4qNocOIRneiHs5v/XTBlQFJr/0Ueb5jaLKRVy2u9qzOM2h5Oe8pIYCIsedzlv4llN+5CfjSuFYuPsK7H5ZLA7ZKjddV9bt+IOEgE1YcPp7k5gODBDH5HfRBLiugSdK8/oeLpm7pK29ulcslSJDYDEkilsEfL1RneWQiD1IyftNCG3OazoU/Xs8dSnamdPOyFV9blPtHkfrxZ6AtLJvGc0vlsgqiHJT1GZl2Ea+WWXMFgde4NFbl671ryEEJUzwptoqljcVVOh86I0dAf5HdNwurQIqll1frs51SYuF4IrTj4nckWzm2vs+jaPh2Jw=="
                    },
                "method": "Deposit"
                }
        self.assertEqual(request, facit, msg="Bad deposit request data is correct")

        self._setup_mock_call(
                response_body="""{"version":"1.1","result":{"data":{"orderid":"2153587137","url":"https://test.trustly.com/_/orderclient.php?SessionID=6414b9f5-65e6-4cbd-9815-f80b7abc2f84&OrderID=2153587137&Locale="},"signature":"EpNO3WCvaY1Afne9qhJUXUdiNrWv9j3CfpNp3fa1ARsv7Mi5cZWsT4UlTgWnuS4/NJ/D8/joKwRdiOHLizv+qeo9AVgE+Gp7pcBuv/uu83gnlaSHuR/9byoJceCbKB/S3EakA0w3lEPCg60RqG4LQcg4VgheL5zh6wIkWMXtxHwg6bPQ+8NVA/Cnd118Oqiz2fqIqHdYfh2MPiqqzLQxca+8QYryTpqGZa8pM9gAqsmzjYKlVLUEe2CXAIs2mnIZ4tsAH3LuXsKzx99D3mtgN1XNLv+k+9q9Qrga7LXS9NozLr/POMZCE+i8/DrbXtFFXtv8oJVKgIVlNjvZnJG0kw==","uuid":"ad4f3dbe-6c1d-11e5-9d5e-0800279bcb52","method":"Deposit"}}""",
                call_uuid="ad4f3dbe-6c1d-11e5-9d5e-0800279bcb52"
                )
        response = self.api.deposit(
                notificationurl='http://notificationurl',
                enduserid='enduser02',
                messageid='message02',
                );

        facit = {
                "version": "1.1",
                "result": {
                    "data": {
                        "orderid": "2153587137",
                        "url": "https://test.trustly.com/_/orderclient.php?SessionID=6414b9f5-65e6-4cbd-9815-f80b7abc2f84&OrderID=2153587137&Locale="
                        },
                    "signature": "EpNO3WCvaY1Afne9qhJUXUdiNrWv9j3CfpNp3fa1ARsv7Mi5cZWsT4UlTgWnuS4/NJ/D8/joKwRdiOHLizv+qeo9AVgE+Gp7pcBuv/uu83gnlaSHuR/9byoJceCbKB/S3EakA0w3lEPCg60RqG4LQcg4VgheL5zh6wIkWMXtxHwg6bPQ+8NVA/Cnd118Oqiz2fqIqHdYfh2MPiqqzLQxca+8QYryTpqGZa8pM9gAqsmzjYKlVLUEe2CXAIs2mnIZ4tsAH3LuXsKzx99D3mtgN1XNLv+k+9q9Qrga7LXS9NozLr/POMZCE+i8/DrbXtFFXtv8oJVKgIVlNjvZnJG0kw==",
                    "uuid": "ad4f3dbe-6c1d-11e5-9d5e-0800279bcb52",
                    "method": "Deposit"
                    }
                }

        self.assertEquals(response.get_uuid(), facit['result']['uuid'], msg="Short deposit response UUID is not correct")
        self.assertEquals(response.get_method(), facit['result']['method'], msg="Short deposit response Method is not correct")
        self.assertEquals(response.get_data(), facit['result']['data'], msg="Short deposit response Data is not correct")
        self.assertEquals(response.get_data('orderid'), facit['result']['data']['orderid'], msg="Short deposit response orderid is not correct")

        facit = {
                "version": "1.1",
                "params": {
                    "Data": {
                        "Username": "testusername",
                        "NotificationURL": "http://notificationurl",
                        "EndUserID": "enduser02",
                        "Password": "testpassword",
                        "MessageID": "message02"
                        },
                    "UUID": "ad4f3dbe-6c1d-11e5-9d5e-0800279bcb52",
                    "Signature": "ppBs0sO96xiMWVkHF0BB3QzUJSCwqNwJhObn5l5nz9wTONddFlvmC44Of1p1ZgpcZcu8Q0MztTLRiijCLTalTVZWAnQ+GXMCOEPh0MVqwoHWo1eyZ+ZUKz6vgxIUmNZeSxfiD10sx2CKZ9gX1zkJnrWzs1juNTLvaQwDMfUZl/BkrMNPPNJebdQDFq1YVOtG2XZsIXBpGIe8XqL/3j7uFclmYJPbUEkuWBYfn2EYfZFG1HRCSqmZ+KW9VBAlb8hJ+QXq4oWodxK12JygI6iId3ZAvOnQZXt1r8DDjJ+0XWzgiUqywaKWY7Lks5zUBRFSJ27EbTOnwlE+bXRNmYCuAA=="
                    },
                "method": "Deposit"
                }

        request = json.loads(mock_api_input_body)
        self.assertEquals(request, facit, msg="Short deposit request data is not correct")

        self._setup_mock_call(
                response_body="""{"version":"1.1","result":{"data":{"orderid":"2153587137","url":"https://test.trustly.com/_/orderclient.php?SessionID=6414b9f5-65e6-4cbd-9815-f80b7abc2f84&OrderID=2153587137&Locale="},"signature":"EpNO3WCvaY1Afne9qhJUXUdiNrWv9j3CfpNp3fa1ARsv7Mi5cZWsT4UlTgWnuS4/NJ/D8/joKwRdiOHLizv+qeo9AVgE+Gp7pcBuv/uu83gnlaSHuR/9byoJceCbKB/S3EakA0w3lEPCg60RqG4LQcg4VgheL5zh6wIkWMXtxHwg6bPQ+8NVA/Cnd118Oqiz2fqIqHdYfh2MPiqqzLQxca+8QYryTpqGZa8pM9gAqsmzjYKlVLUEe2CXAIs2mnIZ4tsAH3LuXsKzx99D3mtgN1XNLv+k+9q9Qrga7LXS9NozLr/POMZCE+i8/DrbXtFFXtv8oJVKgIVlNjvZnJG0kw==","uuid":"ad4f3dbe-6c1d-11e5-9d5e-0800279bcb52","method":"Deposit"}}""",
                call_uuid="ad4f3dbe-6c1d-11e5-9d5e-0800279bcb52"
                )
        response = self.api.deposit(
                notificationurl='http://notificationurl',
                enduserid='enduser02',
                messageid='message02',
                );


        self._setup_mock_call(
                response_body="""{"version":"1.1","result":{"data":{"orderid":"2153587137","url":"https://test.trustly.com/_/orderclient.php?SessionID=6414b9f5-65e6-4cbd-9815-f80b7abc2f84&OrderID=2153587137&Locale="},"signature":"EpNO3WCvaY1Afne9qhJUXUdiNrWv9j3CfpNp3fa1ARsv7Mi5cZWsT4UlTgWnuS4/NJ/D8/joKwRdiOHLizv+qeo9AVgE+Gp7pcBuv/uu83gnlaSHuR/9byoJceCbKB/S3EakA0w3lEPCg60RqG4LQcg4VgheL5zh6wIkWMXtxHwg6bPQ+8NVA/Cnd118Oqiz2fqIqHdYfh2MPiqqzLQxca+8QYryTpqGZa8pM9gAqsmzjYKlVLUEe2CXAIs2mnIZ4tsAH3LuXsKzx99D3mtgN1XNLv+k+9q9Qrga7LXS9NozLr/POMZCE+i8/DrbXtFFXtv8oJVKgIVlNjvZnJG0kw==","uuid":"ad4f3dbe-6c1d-11e5-9d5e-0800279bcb52","method":"Deposit"}}""",
                call_uuid="ad4f3dbe-6c1d-11e5-9d5e-0800279bcb53"
                )
        with self.assertRaises(trustly.exceptions.TrustlyDataError, msg='Short deposit request 2 is unrelated to answer'):
            response = self.api.deposit(
                    notificationurl='http://notificationurl',
                    enduserid='enduser02',
                    messageid='message02',
                    );

        self._teardown_mock_call()

    def testWithdraw(self):
        global mock_api_input_method
        global mock_api_input_url
        global mock_api_input_body

        self._setup_mock_call(
                response_body = """{"result":{"data":{"url":"https://test.trustly.com/_/orderclient.php?SessionID=3d788d4e-3719-4179-b041-527f0d54b3eb&OrderID=2401751195&Locale=en_US","orderid":"2401751195"},"signature":"jHtUIhB/iseyxGMjMT2AWAZgO8ERk7cveytlQKP/85YaX4OpxDsI9Hj8tPJ8hPohgkFeI87fF5ALfTZ2VORazvyiwGLXpUx9NHqClbjCPvlSdtxK7AUkXiWwCWEroWqjSUfBaMjPwFlbK4lM43nDKb7iVC/eyIJzPKayAFtN2BkVM/hkYrHeIhUNCg6Cs+7SM61HgGLhWj/l6WuUMXZPUTpSd9QuLBU/JVB9n6Zz5rlTxnVwoM5nkYRqIv0dGVA962fGKkDJdZj8cXHn8lOZQmm7RcSnN+EmtCbTykjH4zAEpUOgABtcrq5ENIV7PEQ31XiuYnVdFLcQlyjHoKLEng==","uuid":"ad4f3dbe-6c1d-11e5-9d5e-0800279bcb53","method":"Withdraw"},"version":"1.1"}""",
                call_uuid="ad4f3dbe-6c1d-11e5-9d5e-0800279bcb53"
                )

        response = self.api.withdraw(
                notificationurl='http://notificationurl03',
                enduserid='enduserid03',
                messageid='messageid03',
                currency='USD',
                locale='en_US',
                country='UK',
                ip='127.0.0.2',
                templateurl='http://templateurl03',
                clearinghouse='clearinghouse03',
                banknumber='banknumber03',
                accountnumber='accountnumber03',
                firstname='firstname03',
                lastname='lastname03',
                mobilephone='mobilephone03',
                nationalidentificationnumber='nationalidentificationnumber03',
                address='address03',
                holdnotifications=False
                )

        self.assertEqual(response.is_success(), True, msg='Withdraw call is a success')

        request = json.loads(mock_api_input_body)
        facit = {
                "version": "1.1",
                "params": {
                    "Data": {
                        "Username": "testusername",
                        "NotificationURL": "http://notificationurl03",
                        "Currency": "USD",
                        "MessageID": "messageid03",
                        "Attributes": {
                            "ClearingHouse": "clearinghouse03",
                            "MobilePhone": "mobilephone03",
                            "Firstname": "firstname03",
                            "AccountNumber": "accountnumber03",
                            "Locale": "en_US",
                            "Lastname": "lastname03",
                            "Country": "UK",
                            "BankNumber": "banknumber03",
                            "Address": "address03",
                            "TemplateURL": "http://templateurl03",
                            "IP": "127.0.0.2",
                            "NationalIdentificationNumber": "nationalidentificationnumber03"
                            },
                        "Password": "testpassword",
                        "EndUserID": "enduserid03"
                        },
                    "UUID": "ad4f3dbe-6c1d-11e5-9d5e-0800279bcb53",
                    "Signature": "DV8JBv63ObhdBg52FTzHbI8bQpbQHemDZT85mze4KqKi140ZwJ7MtqjBUqqMIeJFeo6AU3t+hC4A1LzU12anbCprr6DWYkzKhjgmYNPfAW/6OFrciWLqggH0IKlvbyDKaMqQ2jv/jstQ+6nZwcuSkOGSQEfYS/22Z00aNYDSIj6YXzM/3+ElybyN6fuU/h94cVQ3nCtJVkv0NwBX4pYZHWM9I8+DuzgUBCdF1PcOCHBC7CkVHldo4aUnyDzdQzjmhvMOI1GuCBdoqt4p+D6rq+FqwCIQRRg9NfK1E8HAi9W2ke8+cLpZN9Jt6NA4R94XOtwKp2ddZI85Djc7/bVjGA=="
                    },
                "method": "Withdraw"
                }
        self.assertEquals(request, facit, msg="Withdraw request data is correct")

        self._teardown_mock_call()

    def testRefund(self):
        global mock_api_input_method
        global mock_api_input_url
        global mock_api_input_body

        self._setup_mock_call(
                response_body = """{"result": {"data": {"orderid": "4034954614","result": "1"},"method": "Refund","signature": "XEvRnWxl6qekCeGA2qfJlt2Y/hy/8wujH2JIM11vBe7WqK4DS4ISvP6KxEuWfzsKmcmgEqd025cvcoh8aXVeRBvV/YXKq/tyA1y5xW+xYQfTGB8uIws9E1TLvYH7pi4sJFEcfesT4FwWIrQNsH7E9RyVUhd+Sg0MWXhv0FJY+pULNhDOV2bkuVoy+ALg2INHorGwJ0D1znk9CO5iGR7a9GTtc7zwRfrLPqfw1uHNL9wO0hE5rPmer+ENoqdWyTE/y7h5/gBJ8MNcsu6cFC00Qf+Ge4Fip9olPuqE5LrAmEMmEC9Frw6+tB7MsyFlKdaIaneJPOGxGSccIaeKEoUZkQ==","uuid": "1fb9bb58-6cf1-11e5-9d5e-0800279bcb51"},"version": "1.1"}""",
                call_uuid="1fb9bb58-6cf1-11e5-9d5e-0800279bcb51"
                )

        response = self.api.refund(
                orderid='4034954614',
                amount='12.05',
                currency='SEK'
                )

        self.assertEqual(response.is_success(), True, msg='Response call is a success')

        request = json.loads(mock_api_input_body)
        facit = {
                "version": "1.1",
                "params": {
                    "Data": {
                        "OrderID": "4034954614",
                        "Currency": "SEK",
                        "Amount": "12.05",
                        "Username": "testusername",
                        "Password": "testpassword"
                        },
                    "UUID": "1fb9bb58-6cf1-11e5-9d5e-0800279bcb51",
                    "Signature": "OuyrszEQDoB0Ngn208V5PwTJT4yib9Qp6Witzh8x2BRflWJ+aGGKzQKkP80pApu3sQV8T0r3Ppdelr93Lb8Tzk38X6sL/KNKWzLg9VjEKFlPBUE7xCt/szAHia4ZV9cOfl5tSGgcNXNKEVWaVsJpvAFh1XUjHyNw2hXG9enkfkffFTLK6p+HO8Pm14SvXfbz2BIslzZb18a2dZkLMSEpS20eC3TAdkRWCCxoEtfn8p01TToFleK/PK/2oV+XcD+DlAI1YJP1Kg9TP9k2zmPJ+PKhgMeFpQPK06+Ag3+x6Ps9vzjVQcS7Yz/bHNAlCap7boJmIZ9LaHBPgi3ZmrmGIA=="
                    },
                "method": "Refund"
                }
        self.assertEquals(request, facit, msg="Refund request data is correct")

        self._teardown_mock_call()

    def testApproveWithdrawal(self):
        global mock_api_input_method
        global mock_api_input_url
        global mock_api_input_body
        return 

        self._setup_mock_call(
                response_body = """""",
                call_uuid="ad4f3dbe-6c1d-11e5-9d5e-0800279bcb55"
                )

        response = self.api.approvewithdrawal(
                )

        self.assertEqual(response.is_success(), True, msg='ApproveWithdrawal call is a success')

        request = json.loads(mock_api_input_body)
        facit = {
                }
        self.assertEquals(request, facit, msg="ApproveWithdrawal request data is correct")

        self._teardown_mock_call()

    def testDenyWithdrawal(self):
        global mock_api_input_method
        global mock_api_input_url
        global mock_api_input_body
        return 

        self._setup_mock_call(
                response_body = """""",
                call_uuid="ad4f3dbe-6c1d-11e5-9d5e-0800279bcb56"
                )

        response = self.api.denywithdrawal(
                )

        self.assertEqual(response.is_success(), True, msg='DenyWithdrawal call is a success')

        request = json.loads(mock_api_input_body)
        facit = {
                }
        self.assertEquals(request, facit, msg="DenyWithdrawal request data is correct")

        self._teardown_mock_call()

    def testRegisterAccount(self):
        global mock_api_input_method
        global mock_api_input_url
        global mock_api_input_body

        self._setup_mock_call(
                response_body = """{"result": {"data": {"accountid": "1520389582","bank": "SEB","clearinghouse": "SWEDEN","descriptor": "*865391"},"method": "RegisterAccount","signature": "CTkQhGtBZaSrkvLP2Ywgr+ZNInvoDux58LL8liWpZ1V0XYbk/AJbMe8mhg+Quw8QoOtcBXyVcm7hPgbBiPOxkb3nx4tFgG40xbTzEze9iUi9xuuIvM1BxqUpinS/1Su155FP28eAsIQpVkmME/qMvuYTCu74Rc7IpZy9fCS+XkOXsJVoF7XOH/PC+jmNQuo8GElJYKhxUB9Xbs7bSCxPPSLG8ykTtwIwAd+6QUHtCCSVS4As1gh53DDAL1cZ5PZeY29IchUwkjm0k7lowb+m8rFG+3eln3fRm4aU8daaky2PZXLT1CqeJxDbgUR2XL5anRZ8xxIOEyA0fDiunNdBpg==","uuid": "fc32a824-6cf1-11e5-9d5e-0800279bcb51"},"version": "1.1"}""",
                call_uuid="fc32a824-6cf1-11e5-9d5e-0800279bcb51"
                )

        response = self.api.registeraccount(
                enduserid='enduserid06',
                clearinghouse='SWEDEN',
                banknumber='5329',
                accountnumber='1865391',
                firstname='firstname06',
                lastname='lastname06',
                mobilephone='mobilephone06',
                nationalidentificationnumber='nationalidentificationnumber06',
                address='address06',
                holdnotifications=False
                )

        self.assertEqual(response.is_success(), True, msg='RegisterAccount call is a success')

        request = json.loads(mock_api_input_body)
        facit = {
                "version": "1.1",
                "params": {
                    "Data": {
                        "Username": "testusername",
                        "ClearingHouse": "SWEDEN",
                        "Firstname": "firstname06",
                        "AccountNumber": "1865391",
                        "Lastname": "lastname06",
                        "BankNumber": "5329",
                        "Attributes": {
                            "NationalIdentificationNumber": "nationalidentificationnumber06",
                            "MobilePhone": "mobilephone06",
                            "Address": "address06"
                            },
                        "Password": "testpassword",
                        "EndUserID": "enduserid06"
                        },
                    "UUID": "fc32a824-6cf1-11e5-9d5e-0800279bcb51",
                    "Signature": "MHij9s0tkznfBemFEXVgmjvmoJ7Z6yJLfPvs6m6fUpuVYZpA/EJvVDtynrRMYMwY3EOuGAulBhQOPir1x4WuAwxfjXcORtLNbmW1ohioOZ5wDztAB7Uh6a3MI1LnzDFCtUn68vXUNH1EA/ZQk9nFLTLTo2O5y+f5IFv2EByBoEWCHxHjLYXsDJ4yl1NTsD3SFCQSXFCiguqr4fNZyDvTP6O1Zhp5mLMfuZs9ttE4SpwmB/isxXpu6DfGWYipDI3K57qD7vrIk1NYbyGEP1becCntZptFXMvb3zwGH6UbWCGALB9Ah3LXxV61sq9e/jISyWFf3KGRmbL9/OvV17LhEw=="
                    },
                "method": "RegisterAccount"
                }
        self.assertEquals(request, facit, msg="RegisterAccount request data is correct")

        self._teardown_mock_call()


    def testSelectAccount(self):
        global mock_api_input_method
        global mock_api_input_url
        global mock_api_input_body

        self._setup_mock_call(
                response_body = """{"result": {"data": {"orderid": "1713267740","url": "https://test.trustly.com/_/orderclient.php?SessionID=7bff4fd5-be43-47da-9167-c596876cd989&OrderID=1713267740&Locale=sv_SE"},"method": "SelectAccount","signature": "H0AJu8uFbxPS76+hnvEfkH6pq/or/WR6s8D0WeRtODtDkJgPvXVJGjMSuKSby2xg46Z+f7G7ceo+KWPz3pw29K+8OZEiJrJrdGRxKrOQZAS7Prr0QcxhqmKXPR+IwLb4yErQ68gHoXzTSfjQYsPMe3zv84wSY/HhZRv/uYXd7a4DzKpQYrIRQMKlbsag3m3j1BeqImz6f8ABMInGUodAJmtyMKP10yt3TmY05ifwvircriJk5mH5q3ep0OLOnE5+UdNsGMusHJT0NtAFDS2wZZg6HWdNUftiqXsB5k6lS7yd7ChGwjhm23BfT0FgyOH1IoMMfG1E/5evgMFoBOkZgg==","uuid": "b0001ec2-6cf2-11e5-9d5e-0800279bcb51"},"version": "1.1"}""",
                call_uuid="b0001ec2-6cf2-11e5-9d5e-0800279bcb51"
                )

        response = self.api.selectaccount(
                notificationurl='http://notificationurl07',
                enduserid='enduserid07',
                messageid='messageid07',
                locale='no_NO',
                country='NO',
                ip='127.0.0.7',
                successurl='http://successurl07',
                urltarget='urltarget07',
                mobilephone='mobilephone07',
                firstname='firstname07',
                lastname='lastname07',
                holdnotifications=True
                )

        self.assertEqual(response.is_success(), True, msg='SelectAccount call is a success')

        request = json.loads(mock_api_input_body)
        facit = {
                "version": "1.1",
                "params": {
                    "Data": {
                        "Username": "testusername",
                        "MessageID": "messageid07",
                        "NotificationURL": "http://notificationurl07",
                        "Attributes": {
                            "MobilePhone": "mobilephone07",
                            "Firstname": "firstname07",
                            "Locale": "no_NO",
                            "IP": "127.0.0.7",
                            "Country": "NO",
                            "URLTarget": "urltarget07",
                            "SuccessURL": "http://successurl07",
                            "Lastname": "lastname07",
                            "HoldNotifications": 1
                            },
                        "Password": "testpassword",
                        "EndUserID": "enduserid07"
                        },
                    "UUID": "b0001ec2-6cf2-11e5-9d5e-0800279bcb51",
                    "Signature": "U9WLj21i4nd8MSaIDBxrxJvqWPPN1VsiZaGJz3Ru5HDS8osc97mg43cSihsArG51GEDPguQD6BGl8mGn3Zt311WdNmyY1/JvSVRjhILxORh3m3aulFPjMOkY2Vi1YLJdTBzKdqcc5R5HzlrVejh0fMkR+QfkaOBwfrfgTgtwXej5MRlZtqCTg0sXsacArBfC16K58B/+PxJCM4KpLKHRMLD4GARgzzvVjg66jji/cMlXFisWMyGMDvJBT4hpIOiIH9unN73fqUz1pzYAsKg1WL22QWFjOjKL5K3Ge+xsXlz5avIuvsfWYGv2ktwZ85hYyCTlNLZ2GhhpycMBM3LhYA=="
                    },
                "method": "SelectAccount"
                }
        self.assertEquals(request, facit, msg="SelectAccount request data is correct")

        self._teardown_mock_call()


    def testAccountPayout(self):
        global mock_api_input_method
        global mock_api_input_url
        global mock_api_input_body

        self._setup_mock_call(
                response_body = """{"result": {"data": {"orderid": "3256646606","result": "1"},"method": "AccountPayout","signature": "YLOwbeiR08ulOk2u4u0c6Ou1QOTLqXpYYSwY+BRzXJnHRxdW5KoJNdIihitcegM2eOxaWVQDmMW+WMcSj0OMsxAPPb9BgGWN26vIxT+tXlXTPHIAvYKI+qLWBxyB9l11ZufxmOKZl7WOpIsRbaQaYaSgVEbpd0HCk550nI6vayH+zQmBuxy3gowfEX1LTNUVrUNPhzYSeQhvCFM5+V7AzX0aaJX9wDFsNDOgJKHwm398KlpZF7+fXaOoDJ97H/4G+w3MdS6yWvn6ydO1jh9RC6sWmCXn25aFhowI5gddePoMGXT8AXN9RMtGsO1a7bhqydo2cjzudJOxMIjokgOGnQ==","uuid": "82cf5fac-6cf3-11e5-9d5e-0800279bcb51"},"version": "1.1"}""",
                call_uuid="82cf5fac-6cf3-11e5-9d5e-0800279bcb51"
                )

        response = self.api.accountpayout(
                notificationurl='http://notificationurl08',
                accountid='1520389582',
                enduserid='enduserid06',
                messageid='messageid08',

                amount='20.08',
                currency='SEK',
                )

        self.assertEqual(response.is_success(), True, msg='AccountPayout call is a success')

        request = json.loads(mock_api_input_body)
        facit = {
                "version": "1.1",
                "params": {
                    "Data": {
                        "Username": "testusername",
                        "MessageID": "messageid08",
                        "Currency": "SEK",
                        "Amount": "20.08",
                        "NotificationURL": "http://notificationurl08",
                        "Password": "testpassword",
                        "EndUserID": "enduserid06",
                        "AccountID": "1520389582"
                        },
                    "UUID": "82cf5fac-6cf3-11e5-9d5e-0800279bcb51",
                    "Signature": "Uy4/fyh0B/ufYPRFVTR7WcXbbsLFsYHblz34V5+VBftmhqJrAsVTGCK3Thc4r363QBdn/pughYZsKWZgSjeJZ97dyKTBvIgQRdpwmCqKIiWxC1HW+5glQlIObEO9+VBUkhnm9NDStGXdAsq6W0B8W6YKc5RtVZh3KLH8huYIDg0f9bf7EK7syAIda2wb4DbOxSXTTwpELskiwAFc/3s02d2MZ3LkA20AAFPwUXlXLzdtLnBRhfhiR2zkpmLlKLYr9zYiRqTNdjeN1jEJoV/LWp6pnpPCtiAKJxDOplvuGIX6tjSTa3OWSi1p9arn379anQXB8MHqhefUmaN/S7d+0g=="
                    },
                "method": "AccountPayout"
                }
        self.assertEquals(request, facit, msg="AccountPayout request data is correct")

        self._teardown_mock_call()

    def testCapture(self):
        global mock_api_input_method
        global mock_api_input_url
        global mock_api_input_body

        self._setup_mock_call(
                response_body = """{"version":"1.1","result":{"method":"Capture","data":{"orderid":"4034954614","result":"1"},"signature":"OipqfPNH/neINNSKKTa+hltMtrP+m+XLWc/tEe7RjjkVn5zCcRkwaAWifJn0N9oDr46ksDMnWqjBWnQ3xQL86bxLTA7gZWgTddjCRlDgtaHwtPg83L24z5iRQ95+0m2qBBrA15FQXSa1WLYIC6IawB7eS99vKMHPH2VlPv4uKDiBiac7Atm5tJfK+llIBQ7KXahHjKhUi84B38J7tnklf+ClxV/KaFX5Gaw/wJUlJVDM6CHpu3bWzYx86lB1GUyNXnfOvGEHxU5+5ILAJiYsrEUGx05s/Y2rSEBS6Bjj4piJtMrZzuOqDJIKYxN5cgX6+GZv3tGABuUlKuvwuKT66A==","uuid":"ed7d6aca-6cfc-11e5-9d5e-0800279bcb51"}}""",
                call_uuid="ed7d6aca-6cfc-11e5-9d5e-0800279bcb51"
                )

        response = self.api.capture(
                orderid='4034954614',
                amount='20.09',
                currency='SEK'
                )

        self.assertEqual(response.is_success(), True, msg='Capture call is a success')

        request = json.loads(mock_api_input_body)
        facit = {
                "version": "1.1",
                "params": {
                    "Data": {
                        "OrderID": "4034954614",
                        "Currency": "SEK",
                        "Amount": "20.09",
                        "Username": "testusername",
                        "Password": "testpassword"
                        },
                    "UUID": "ed7d6aca-6cfc-11e5-9d5e-0800279bcb51",
                    "Signature": "UnBeDRYEvwc6tDikWcBJryaEWmsW7/FjM7SDJOIpRFiZw0Gg64SUDIiJN6RF3SqNpeHlPWYUM9E6RzpXFqZe6zrs/YKSbuueENQQl7qhlcSjS+tio1DIUFMNkYTxDfZLccUBrPQdmC84QasOJ1uJI1TJ1FOfFkpr2AlJNEyyEtS9zyG1Tz2xhfsAbARQS9f0NFb6TMax5VE3yynY14owDB8FRGnh512GkXOXkwwfjIcsjRWrzRgV5jcEKDi3ENcOPM/FvZiD9U8yEfmwWK30CjNsQJoUX/b5mPVKLD/5nKC3S4JkPWbv7ZyhB9AzBelVAJn8a0hHnG6DX47fCDmCqA=="
                    },
                "method": "Capture"
                }
        self.assertEquals(request, facit, msg="Capture request data is correct")

        self._teardown_mock_call()

    def testVoid(self):
        global mock_api_input_method
        global mock_api_input_url
        global mock_api_input_body

        self._setup_mock_call(
                response_body = """{"version":"1.1","result":{"signature":"Iw8Mz4Odt09iOmUHhRjCAlvULT5IWNy0uYzPdYy9fp4AgeVFf/p/Lfk0bzHScRB0SNgdLkXi5ljmpFPw4pJ7UWovDIZt8jzhUycTtejBRe7qDH8kpUeUqeps2VYTxusS5qEx8fd62JwLI92DDpmKgw+toRkNE0s+bMsMQQosO4593yEbG2VGy8TfkpeZY/Ui9XOBFI5ZVUnpZuls3q+pAPJwKvBcEc7r6VKKOyIWqZ1lCLtVeqlQz99jZvGphbNQGc6LVoY3pE/PdSKZP1P4n/htBNBnTbGyH5UGDuqX+WxtK9IrweblVnOtxp36JrT9c6YP/USS877Tc97sI7HiMQ==","data":{"orderid":"4034954614","result":"1"},"method":"Void","uuid":"ed7d6aca-6cfc-11e5-9d5e-0800279bcb51"}}""",
                call_uuid="ed7d6aca-6cfc-11e5-9d5e-0800279bcb51"
                )

        response = self.api.void(
                orderid='4034954614'
                )

        self.assertEqual(response.is_success(), True, msg='Void call is a success')

        request = json.loads(mock_api_input_body)
        facit = {
                "version": "1.1",
                "params": {
                    "Data": {
                        "OrderID": "4034954614",
                        "Username": "testusername",
                        "Password": "testpassword"
                        },
                    "UUID": "ed7d6aca-6cfc-11e5-9d5e-0800279bcb51",
                    "Signature": "MwZQPw1apgnuhECZzrgxYKvc8e3mWc78yw5OrYREqBk/0jLNYXOC+hdfc7FLtmOh9ygxfA8hgEjM81YbrbrgjpAK1RCBTXjD5a+su8Y1Z+gdBOPbWyo74iKlvCUAGi+5VVYq3OJjaAM8FGlYMzcKoEDRfhStJox696ZPCwXW8NhxEl2jFQzw2XQEPnijtKhAU6rrz94oqv1mP6pBGiJtZBT67CMZeSVYg9KUyAhq1HvJmqluoLV1n9sHtKMlFloiutcpacm8sZ7bwAZjY2OEM1XnSbKQdFfSVxYUC1uFc7ARJc1iGr4Cs+E7SQNh1kQaHMze8IrhK6e2/poAOggk+w=="
                    },
                "method": "Void"
                }
        self.assertEquals(request, facit, msg="Void request data is correct")

        self._teardown_mock_call()

    def testP2P(self):
        global mock_api_input_method
        global mock_api_input_url
        global mock_api_input_body

        self._setup_mock_call(
                response_body = """{"version":"1.1","result":{"method":"P2P","signature":"Mahio5sQymwl2gQ6Vfb0c1wG9WibD/tQ49LcdMIFWQMVKqvJkb68r6W0ODFPBLGwAkvu/ygiP17jgMF1M/ndLz0ICkYN0IxxBlTrmueTOdq480z4J040Sj6/u0F5eziTkX+p4zrormgxrF5ty4ZBcToG1xtNPMNamSyeYgP56+AwpLcKAz/jltgFfYE/SXZTl4/xn/668YTvrvGGhx7Wvs+oOybn1M1jN5X1DvQvj6avO0/Bk7bE8D/GXwRhqJ+8HGYxeFs0wM2mCY5ao7spBm4LrA5Y1jsTxtvL6SsPJeRclFLD//LyW3WCGhXzhL1IO9mf7HNFsleodHpG1vnpOw==","data":{"url":"https://test.trustly.com/b9a212c9-d279-4504-b384-3eaed3f407be","orderid":"2120043291"},"uuid":"ad4f3dbe-6c1d-11e5-9d5e-0800279bcb5b"}}""",
                call_uuid="ad4f3dbe-6c1d-11e5-9d5e-0800279bcb5b"
                )

        response = self.api.p2p(
                notificationurl='http://notificationurl04',
                enduserid='enduser04',
                messageid='message04',
                locale='en_US',
                amount='20.04',
                currency='SEK',
                country='SE',
                ip='127.0.0.4',
                successurl='http://successurl04',
                failurl='http://failurl04',
                templateurl='http://templateurl04',
                urltarget='urltarget04',
                mobilephone='mobilephone04',
                firstname='firstname04',
                lastname='lastname04',
                nationalidentificationnumber='nationalidentificationnumber04',
                shopperstatement='shopperstatement04',
                suggestedminamount='10.04',
                suggestedmaxamount='100.04',
                integrationmodule='integrationmodule04',
                holdnotifications=True
                )

        self.assertEqual(response.is_success(), True, msg='P2P call is a success')

        request = json.loads(mock_api_input_body)
        facit = {
                "version": "1.1",
                "params": {
                    "Data": {
                        "Username": "testusername",
                        "MessageID": "message04",
                        "NotificationURL": "http://notificationurl04",
                        "Attributes": {
                            "ShopperStatement": "shopperstatement04",
                            "IP": "127.0.0.4",
                            "MobilePhone": "mobilephone04",
                            "Firstname": "firstname04",
                            "Locale": "en_US",
                            "Country": "SE",
                            "SuggestedMaxAmount": "100.04",
                            "Currency": "SEK",
                            "Amount": "20.04",
                            "URLTarget": "urltarget04",
                            "SuccessURL": "http://successurl04",
                            "Lastname": "lastname04",
                            "FailURL": "http://failurl04",
                            "SuggestedMinAmount": "10.04",
                            "TemplateURL": "http://templateurl04",
                            "IntegrationModule": "integrationmodule04",
                            "HoldNotifications": 1,
                            "NationalIdentificationNumber": "nationalidentificationnumber04"
                            },
                        "Password": "testpassword",
                        "EndUserID": "enduser04"
                        },
                    "UUID": "ad4f3dbe-6c1d-11e5-9d5e-0800279bcb5b",
                    "Signature": "Sgi3vZSuajoUGvOeYzQwCeWHRbL428MC7/ZGB0xKIM0+d5E1G9mpYTxK7/VgvETcYzgl16E+phdn/VxLWMDNQnEs6T+7ejXsa2fMhzrEHqKNbR4jmuYESXWxJUb0v7wExD2KjvL2RBQSmVurigkpe2tJrLP1zbI/lU1weNm20VMZGnLBVZxjp2gXAHE7JgS9rDzZidkYZsvVsOExcEfaTzkCFighLC1xSOel8LDKJayAWKIlHNiTUrVh3m2hypPbtzY4tu8otbrR1jj4G+npTN3phWzZlrUU2cPNuDwjQvhel3PLKdH+yOwSVVgNeVwzQb77QYgYJra52jCFHDugcg=="
                    },
                "method": "P2P"
                }
        self.assertEquals(request, facit, msg="P2P request data is correct")

        self._teardown_mock_call()


if __name__ == "__main__":
    unittest.main()

