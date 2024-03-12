# Copyright (c) 2012 Andy Davidoff http://www.disruptek.com/
# Copyright (c) 2010 Jason R. Coombs http://www.jaraco.com/
# Copyright (c) 2008 Chris Moyer http://coredumped.org/
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import urllib
import uuid
from boto.connection import AWSQueryConnection
from boto.fps.exception import ResponseErrorFactory
from boto.fps.response import ResponseFactory
import boto.fps.response

__all__ = ['FPSConnection']

decorated_attrs = ('action', 'response')


def add_attrs_from(func, to):
    for attr in decorated_attrs:
        setattr(to, attr, getattr(func, attr, None))
    return to


def complex_amounts(*fields):
    def decorator(func):
        def wrapper(self, *args, **kw):
            for field in filter(kw.has_key, fields):
                amount = kw.pop(field)
                kw[field + '.Value'] = getattr(amount, 'Value', str(amount))
                kw[field + '.CurrencyCode'] = getattr(amount, 'CurrencyCode',
                                                      self.currencycode)
            return func(self, *args, **kw)
        wrapper.__doc__ = "{0}\nComplex Amounts: {1}".format(func.__doc__,
                                                 ', '.join(fields))
        return add_attrs_from(func, to=wrapper)
    return decorator


def requires(*groups):

    def decorator(func):

        def wrapper(*args, **kw):
            hasgroup = lambda x: len(x) == len(filter(kw.has_key, x))
            if 1 != len(filter(hasgroup, groups)):
                message = ' OR '.join(['+'.join(g) for g in groups])
                message = "{0} requires {1} argument(s)" \
                          "".format(getattr(func, 'action', 'Method'), message)
                raise KeyError(message)
            return func(*args, **kw)
        message = ' OR '.join(['+'.join(g) for g in groups])
        wrapper.__doc__ = "{0}\nRequired: {1}".format(func.__doc__,
                                                           message)
        return add_attrs_from(func, to=wrapper)
    return decorator


def needs_caller_reference(func):

    def wrapper(*args, **kw):
        kw.setdefault('CallerReference', uuid.uuid4())
        return func(*args, **kw)
    wrapper.__doc__ = "{0}\nUses CallerReference, defaults " \
                      "to uuid.uuid4()".format(func.__doc__)
    return add_attrs_from(func, to=wrapper)


def api_action(*api):

    def decorator(func):
        action = ''.join(api or map(str.capitalize, func.__name__.split('_')))
        response = ResponseFactory(action)
        if hasattr(boto.fps.response, action + 'Response'):
            response = getattr(boto.fps.response, action + 'Response')

        def wrapper(self, *args, **kw):
            return func(self, action, response, *args, **kw)
        wrapper.action, wrapper.response = action, response
        wrapper.__doc__ = "FPS {0} API call\n{1}".format(action,
                                                         func.__doc__)
        return wrapper
    return decorator


class FPSConnection(AWSQueryConnection):

    APIVersion = '2010-08-28'
    ResponseError = ResponseErrorFactory
    currencycode = 'USD'

    def __init__(self, *args, **kw):
        self.currencycode = kw.pop('CurrencyCode', self.currencycode)
        kw.setdefault('host', 'fps.sandbox.amazonaws.com')
        super(FPSConnection, self).__init__(*args, **kw)

    def _required_auth_capability(self):
        return ['fps']

    @needs_caller_reference
    @complex_amounts('SettlementAmount')
    @requires(['CreditInstrumentId', 'SettlementAmount.Value',
               'SenderTokenId',      'SettlementAmount.CurrencyCode'])
    @api_action()
    def settle_debt(self, action, response, **kw):
        """
        Allows a caller to initiate a transaction that atomically transfers
        money from a sender's payment instrument to the recipient, while
        decreasing corresponding debt balance.
        """
        return self.get_object(action, kw, response)

    @requires(['TransactionId'])
    @api_action()
    def get_transaction_status(self, action, response, **kw):
        """
        Gets the latest status of a transaction.
        """
        return self.get_object(action, kw, response)

    @requires(['StartDate'])
    @api_action()
    def get_account_activity(self, action, response, **kw):
        """
        Returns transactions for a given date range.
        """
        return self.get_object(action, kw, response)

    @requires(['TransactionId'])
    @api_action()
    def get_transaction(self, action, response, **kw):
        """
        Returns all details of a transaction.
        """
        return self.get_object(action, kw, response)

    @api_action()
    def get_outstanding_debt_balance(self, action, response):
        """
        Returns the total outstanding balance for all the credit instruments
        for the given creditor account.
        """
        return self.get_object(action, {}, response)

    @requires(['PrepaidInstrumentId'])
    @api_action()
    def get_prepaid_balance(self, action, response, **kw):
        """
        Returns the balance available on the given prepaid instrument.
        """
        return self.get_object(action, kw, response)

    @api_action()
    def get_total_prepaid_liability(self, action, response):
        """
        Returns the total liability held by the given account corresponding to
        all the prepaid instruments owned by the account.
        """
        return self.get_object(action, {}, response)

    @api_action()
    def get_account_balance(self, action, response):
        """
        Returns the account balance for an account in real time.
        """
        return self.get_object(action, {}, response)

    @needs_caller_reference
    @requires(['PaymentInstruction', 'TokenType'])
    @api_action()
    def install_payment_instruction(self, action, response, **kw):
        """
        Installs a payment instruction for caller.
        """
        return self.get_object(action, kw, response)

    @needs_caller_reference
    @requires(['returnURL', 'pipelineName'])
    def cbui_url(self, **kw):
        """
        Generate a signed URL for the Co-Branded service API given arguments as
        payload.
        """
        sandbox = 'sandbox' in self.host and 'payments-sandbox' or 'payments'
        endpoint = 'authorize.{0}.amazon.com'.format(sandbox)
        base = '/cobranded-ui/actions/start'

        validpipelines = ('SingleUse', 'MultiUse', 'Recurring', 'Recipient',
                          'SetupPrepaid', 'SetupPostpaid', 'EditToken')
        assert kw['pipelineName'] in validpipelines, "Invalid pipelineName"
        kw.update({
            'signatureMethod':  'HmacSHA256',
            'signatureVersion': '2',
        })
        kw.setdefault('callerKey', self.aws_access_key_id)

        safestr = lambda x: x is not None and str(x) or ''
        safequote = lambda x: urllib.quote(safestr(x), safe='~')
        payload = sorted([(k, safequote(v)) for k, v in kw.items()])

        encoded = lambda p: '&'.join([k + '=' + v for k, v in p])
        canonical = '\n'.join(['GET', endpoint, base, encoded(payload)])
        signature = self._auth_handler.sign_string(canonical)
        payload += [('signature', safequote(signature))]
        payload.sort()

        return 'https://{0}{1}?{2}'.format(endpoint, base, encoded(payload))

    @needs_caller_reference
    @complex_amounts('TransactionAmount')
    @requires(['SenderTokenId', 'TransactionAmount.Value',
                                'TransactionAmount.CurrencyCode'])
    @api_action()
    def reserve(self, action, response, **kw):
        """
        Reserve API is part of the Reserve and Settle API conjunction that
        serve the purpose of a pay where the authorization and settlement have
        a timing difference.
        """
        return self.get_object(action, kw, response)

    @needs_caller_reference
    @complex_amounts('TransactionAmount')
    @requires(['SenderTokenId', 'TransactionAmount.Value',
                                'TransactionAmount.CurrencyCode'])
    @api_action()
    def pay(self, action, response, **kw):
        """
        Allows calling applications to move money from a sender to a recipient.
        """
        return self.get_object(action, kw, response)

    @requires(['TransactionId'])
    @api_action()
    def cancel(self, action, response, **kw):
        """
        Cancels an ongoing transaction and puts it in cancelled state.
        """
        return self.get_object(action, kw, response)

    @complex_amounts('TransactionAmount')
    @requires(['ReserveTransactionId', 'TransactionAmount.Value',
                                       'TransactionAmount.CurrencyCode'])
    @api_action()
    def settle(self, action, response, **kw):
        """
        The Settle API is used in conjunction with the Reserve API and is used
        to settle previously reserved transaction.
        """
        return self.get_object(action, kw, response)

    @complex_amounts('RefundAmount')
    @requires(['TransactionId',   'RefundAmount.Value',
               'CallerReference', 'RefundAmount.CurrencyCode'])
    @api_action()
    def refund(self, action, response, **kw):
        """
        Refunds a previously completed transaction.
        """
        return self.get_object(action, kw, response)

    @requires(['RecipientTokenId'])
    @api_action()
    def get_recipient_verification_status(self, action, response, **kw):
        """
        Returns the recipient status.
        """
        return self.get_object(action, kw, response)

    @requires(['CallerReference'], ['TokenId'])
    @api_action()
    def get_token_by_caller(self, action, response, **kw):
        """
        Returns the details of a particular token installed by this calling
        application using the subway co-branded UI.
        """
        return self.get_object(action, kw, response)

    @requires(['UrlEndPoint', 'HttpParameters'])
    @api_action()
    def verify_signature(self, action, response, **kw):
        """
        Verify the signature that FPS sent in IPN or callback urls.
        """
        return self.get_object(action, kw, response)

    @api_action()
    def get_tokens(self, action, response, **kw):
        """
        Returns a list of tokens installed on the given account.
        """
        return self.get_object(action, kw, response)

    @requires(['TokenId'])
    @api_action()
    def get_token_usage(self, action, response, **kw):
        """
        Returns the usage of a token.
        """
        return self.get_object(action, kw, response)

    @requires(['TokenId'])
    @api_action()
    def cancel_token(self, action, response, **kw):
        """
        Cancels any token installed by the calling application on its own
        account.
        """
        return self.get_object(action, kw, response)

    @needs_caller_reference
    @complex_amounts('FundingAmount')
    @requires(['PrepaidInstrumentId', 'FundingAmount.Value',
               'SenderTokenId',       'FundingAmount.CurrencyCode'])
    @api_action()
    def fund_prepaid(self, action, response, **kw):
        """
        Funds the prepaid balance on the given prepaid instrument.
        """
        return self.get_object(action, kw, response)

    @requires(['CreditInstrumentId'])
    @api_action()
    def get_debt_balance(self, action, response, **kw):
        """
        Returns the balance corresponding to the given credit instrument.
        """
        return self.get_object(action, kw, response)

    @needs_caller_reference
    @complex_amounts('AdjustmentAmount')
    @requires(['CreditInstrumentId', 'AdjustmentAmount.Value',
                                     'AdjustmentAmount.CurrencyCode'])
    @api_action()
    def write_off_debt(self, action, response, **kw):
        """
        Allows a creditor to write off the debt balance accumulated partially
        or fully at any time.
        """
        return self.get_object(action, kw, response)

    @requires(['SubscriptionId'])
    @api_action()
    def get_transactions_for_subscription(self, action, response, **kw):
        """
        Returns the transactions for a given subscriptionID.
        """
        return self.get_object(action, kw, response)

    @requires(['SubscriptionId'])
    @api_action()
    def get_subscription_details(self, action, response, **kw):
        """
        Returns the details of Subscription for a given subscriptionID.
        """
        return self.get_object(action, kw, response)

    @needs_caller_reference
    @complex_amounts('RefundAmount')
    @requires(['SubscriptionId'])
    @api_action()
    def cancel_subscription_and_refund(self, action, response, **kw):
        """
        Cancels a subscription.
        """
        message = "If you specify a RefundAmount, " \
                  "you must specify CallerReference."
        assert not 'RefundAmount.Value' in kw \
                or 'CallerReference' in kw, message
        return self.get_object(action, kw, response)

    @requires(['TokenId'])
    @api_action()
    def get_payment_instruction(self, action, response, **kw):
        """
        Gets the payment instruction of a token.
        """
        return self.get_object(action, kw, response)
