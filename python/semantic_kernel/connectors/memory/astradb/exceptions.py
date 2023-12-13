class AstraDbException(Exception):
    """The base exception class for all Astra client exceptions."""

class AstraDBProtocolError(AstraDbException):
    """Raised when something unexpected happens mid-request/response."""

class OpenApiException(AstraDbException):
    """The base exception class for all OpenAPIExceptions"""

class ApiException(OpenApiException):
    def __init__(self, status=None, reason=None, http_resp=None):
        if http_resp:
            self.status = http_resp.status
            self.reason = http_resp.reason
            self.body = http_resp.data
            self.headers = http_resp.getheaders()
        else:
            self.status = status
            self.reason = reason
            self.body = None
            self.headers = None

    def __str__(self):
        """Custom error messages for exception"""
        error_message = "({0})\n" "Reason: {1}\n".format(self.status, self.reason)
        if self.headers:
            error_message += "HTTP response headers: {0}\n".format(self.headers)

        if self.body:
            error_message += "HTTP response body: {0}\n".format(self.body)

        return error_message

class ForbiddenException(ApiException):
    def __init__(self, status=None, reason=None, http_resp=None):
        super(ForbiddenException, self).__init__(status, reason, http_resp)

class ServiceException(ApiException):
    def __init__(self, status=None, reason=None, http_resp=None):
        super(ServiceException, self).__init__(status, reason, http_resp)
