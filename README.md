Trustly Python Client
=====================

This is an example implementation of communication with the Trustly API using
Python. It implements the standard Payments API as well as gives stubs for
executing calls against the API used by the backoffice.

For full documentation on the Trustly API internals visit our developer
website: http://trustly.com/developer . All information about software flows and
call patters can be found on that site. The documentation within this code will
only cover the code itself, not how you use the Trustly API.

This code is provided as-is, use it as inspiration, reference or drop it
directly into your own project and use it.

If you find problem in the code or want to extend it feel free to fork it and send us
a pull request.

This code is written for python 2.7.

Overview
========

The code provided wrappers for calling the trustly API. Create an instance of
the API call with you merchant criterias and use the stubs in that class for
calling the API. The API will default to communicate with https://trustly.com,
override the `host` parameter for the constructor to comminicate with
test.trustly.com instead.

When processing an incoming notification the `handle_notification()` method of the
API will help with parsing and verifying the message signature, use `notification_response()`
to build a proper response object

The examples below represent a very basic usage of the calls. A minimum of error
handling around this code would be to check for the following exceptions during
processing.

- `TrustlyConnectionError`

  Thrown when unable to communicate with the Trustly API. This can be due to
  Internet or other forms of service errors.

- `TrustlyDataError`

  Thrown upon various problems with the API returned data. For instance when a
  responding message contains a different UUID then the sent message or when the
  response structure is incomplete.

- `TrustlySignatureError`

  Issued when the authenticity of messages cannot be verified. If ever this
  exception is caught the data in the communication should be voided as it can be
  a forgery.

Example deposit call
--------------------

    import trustly.api.signed

    trustly_username = 'YourUsername'
    trustly_password = 'YourPassword'
    trustly_pem = '/location/to/your/pem-file'

    api = trustly.api.signed.SignedAPI(merchant_privatekey=trustly_pem,
            username=trustly_username, password=trustly_password)

    deposit = api.deposit(
        notificationurl='https://example.com/trustlynotification',
        enduserid='user@email.com',
        messageid='abb424decb1',
        locale='sv_SE',
        amount='12.34',
        currency='EUR',
        country='SE',
        firstname='John',
        lastname='Doe'
        )

    iframe_url=deposit.get_result('data').get('url')

Example notification processing
-------------------------------

    request=api.handle_notification(notification_body))
    # FIXME Handle the incoming notification data here
    notifyresponse=api.notification_response(request, True)

    # Write json response to the output stream for the web server
    req.write(notifyresponse.json())
