from boto.exception import BotoServerError


class ResponseErrorFactory(BotoServerError):

    def __new__(cls, *args, **kw):
        error = BotoServerError(*args, **kw)
        newclass = globals().get(error.error_code, ResponseError)
        obj = newclass.__new__(newclass, *args, **kw)
        obj.__dict__.update(error.__dict__)
        return obj


class ResponseError(BotoServerError):
    """Undefined response error.
    """
    retry = False

    def __repr__(self):
        return '{0}({1}, {2},\n\t{3})'.format(self.__class__.__name__,
                                              self.status, self.reason,
                                              self.error_message)

    def __str__(self):
        return 'FPS Response Error: {0.status} {0.__class__.__name__} {1}\n' \
               '{2}\n' \
               '{0.error_message}'.format(self,
                                          self.retry and '(Retriable)' or '',
                                          self.__doc__.strip())


class RetriableResponseError(ResponseError):
    retry = True


class AccessFailure(RetriableResponseError):
    """Account cannot be accessed.
    """


class AccountClosed(RetriableResponseError):
    """Account is not active.
    """


class AccountLimitsExceeded(RetriableResponseError):
    """The spending or receiving limit on the account is exceeded.
    """


class AmountOutOfRange(ResponseError):
    """The transaction amount is more than the allowed range.
    """


class AuthFailure(RetriableResponseError):
    """AWS was not able to validate the provided access credentials.
    """


class ConcurrentModification(RetriableResponseError):
    """A retriable error can happen when two processes try to modify the
       same data at the same time.
    """


class DuplicateRequest(ResponseError):
    """A different request associated with this caller reference already
       exists.
    """


class InactiveInstrument(ResponseError):
    """Payment instrument is inactive.
    """


class IncompatibleTokens(ResponseError):
    """The transaction could not be completed because the tokens have
       incompatible payment instructions.
    """


class InstrumentAccessDenied(ResponseError):
    """The external calling application is not the recipient for this
       postpaid or prepaid instrument.
    """


class InstrumentExpired(ResponseError):
    """The prepaid or the postpaid instrument has expired.
    """


class InsufficientBalance(RetriableResponseError):
    """The sender, caller, or recipient's account balance has
       insufficient funds to complete the transaction.
    """


class InternalError(RetriableResponseError):
    """A retriable error that happens due to some transient problem in
       the system.
    """


class InvalidAccountState(RetriableResponseError):
    """The account is either suspended or closed.
    """


class InvalidAccountState_Caller(RetriableResponseError):
    """The developer account cannot participate in the transaction.
    """


class InvalidAccountState_Recipient(RetriableResponseError):
    """Recipient account cannot participate in the transaction.
    """


class InvalidAccountState_Sender(RetriableResponseError):
    """Sender account cannot participate in the transaction.
    """


class InvalidCallerReference(ResponseError):
    """The Caller Reference does not have a token associated with it.
    """


class InvalidClientTokenId(ResponseError):
    """The AWS Access Key Id you provided does not exist in our records.
    """


class InvalidDateRange(ResponseError):
    """The end date specified is before the start date or the start date
       is in the future.
    """


class InvalidParams(ResponseError):
    """One or more parameters in the request is invalid.
    """


class InvalidPaymentInstrument(ResponseError):
    """The payment method used in the transaction is invalid.
    """


class InvalidPaymentMethod(ResponseError):
    """Specify correct payment method.
    """


class InvalidRecipientForCCTransaction(ResponseError):
    """This account cannot receive credit card payments.
    """


class InvalidSenderRoleForAccountType(ResponseError):
    """This token cannot be used for this operation.
    """


class InvalidTokenId(ResponseError):
    """You did not install the token that you are trying to cancel.
    """


class InvalidTokenId_Recipient(ResponseError):
    """The recipient token specified is either invalid or canceled.
    """


class InvalidTokenId_Sender(ResponseError):
    """The sender token specified is either invalid or canceled or the
       token is not active.
    """


class InvalidTokenType(ResponseError):
    """An invalid operation was performed on the token, for example,
       getting the token usage information on a single use token.
    """


class InvalidTransactionId(ResponseError):
    """The specified transaction could not be found or the caller did not
       execute the transaction or this is not a Pay or Reserve call.
    """


class InvalidTransactionState(ResponseError):
    """The transaction is not complete, or it has temporarily failed.
    """


class NotMarketplaceApp(RetriableResponseError):
    """This is not an marketplace application or the caller does not
       match either the sender or the recipient.
    """


class OriginalTransactionFailed(ResponseError):
    """The original transaction has failed.
    """


class OriginalTransactionIncomplete(RetriableResponseError):
    """The original transaction is still in progress.
    """


class PaymentInstrumentNotCC(ResponseError):
    """The payment method specified in the transaction is not a credit
       card.  You can only use a credit card for this transaction.
    """


class PaymentMethodNotDefined(ResponseError):
    """Payment method is not defined in the transaction.
    """


class PrepaidFundingLimitExceeded(RetriableResponseError):
    """An attempt has been made to fund the prepaid instrument
       at a level greater than its recharge limit.
    """


class RefundAmountExceeded(ResponseError):
    """The refund amount is more than the refundable amount.
    """


class SameSenderAndRecipient(ResponseError):
    """The sender and receiver are identical, which is not allowed.
    """


class SameTokenIdUsedMultipleTimes(ResponseError):
    """This token is already used in earlier transactions.
    """


class SenderNotOriginalRecipient(ResponseError):
    """The sender in the refund transaction is not
       the recipient of the original transaction.
    """


class SettleAmountGreaterThanDebt(ResponseError):
    """The amount being settled or written off is
       greater than the current debt.
    """


class SettleAmountGreaterThanReserveAmount(ResponseError):
    """The amount being settled is greater than the reserved amount.
    """


class SignatureDoesNotMatch(ResponseError):
    """The request signature calculated by Amazon does not match the
       signature you provided.
    """


class TokenAccessDenied(ResponseError):
    """Permission to cancel the token is denied.
    """


class TokenNotActive(ResponseError):
    """The token is canceled.
    """


class TokenNotActive_Recipient(ResponseError):
    """The recipient token is canceled.
    """


class TokenNotActive_Sender(ResponseError):
    """The sender token is canceled.
    """


class TokenUsageError(ResponseError):
    """The token usage limit is exceeded.
    """


class TransactionDenied(ResponseError):
    """The transaction is not allowed.
    """


class TransactionFullyRefundedAlready(ResponseError):
    """The transaction has already been completely refunded.
    """


class TransactionTypeNotRefundable(ResponseError):
    """You cannot refund this transaction.
    """


class UnverifiedAccount_Recipient(ResponseError):
    """The recipient's account must have a verified bank account or a
       credit card before this transaction can be initiated.
    """


class UnverifiedAccount_Sender(ResponseError):
    """The sender's account must have a verified U.S.  credit card or
       a verified U.S bank account before this transaction can be
       initiated.
    """


class UnverifiedBankAccount(ResponseError):
    """A verified bank account should be used for this transaction.
    """


class UnverifiedEmailAddress_Caller(ResponseError):
    """The caller account must have a verified email address.
    """


class UnverifiedEmailAddress_Recipient(ResponseError):
    """The recipient account must have a verified
       email address for receiving payments.
    """


class UnverifiedEmailAddress_Sender(ResponseError):
    """The sender account must have a verified
       email address for this payment.
    """
