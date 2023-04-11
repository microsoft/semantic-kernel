// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Diagnostics;

/// <summary>
/// Contains the values of status codes defined for HTTP in the response to an HTTP request.
/// </summary>
[SuppressMessage("Design", "CA1069:Enums values should not be duplicated", Justification = "<Pending>")]
internal enum HttpStatusCodeType
{
    /// <summary>
    /// The server has received the request headers and the client should proceed to send the request body.
    /// </summary>
    Continue = 100,

    /// <summary>
    /// The server is switching protocols according to the Upgrade header sent by the client.
    /// </summary>
    SwitchingProtocols = 101,

    /// <summary>
    /// The server is processing the request, but has not completed it yet.
    /// </summary>
    Processing = 102,

    /// <summary>
    /// The server is sending some hints about the response before the final status code.
    /// </summary>
    EarlyHints = 103,

    /// <summary>
    /// The request has succeeded and the response contains the requested resource.
    /// </summary>
    OK = 200,

    /// <summary>
    /// The request has been fulfilled and a new resource has been created.
    /// </summary>
    Created = 201,

    /// <summary>
    /// The request has been accepted for further processing, but the processing has not been completed.
    /// </summary>
    Accepted = 202,

    /// <summary>
    /// The server is returning a response from a different source than the requested one, but the response is still valid.
    /// </summary>
    NonAuthoritativeInformation = 203,

    /// <summary>
    /// The request has been successfully processed, but the server does not need to return any content.
    /// </summary>
    NoContent = 204,

    /// <summary>
    /// The server has fulfilled the request and the client should reset the document view.
    /// </summary>
    ResetContent = 205,

    /// <summary>
    /// The server is returning a partial response to a range request.
    /// </summary>
    PartialContent = 206,

    /// <summary>
    /// The server is returning a response that contains multiple status codes for different parts of the request.
    /// </summary>
    MultiStatus = 207,

    /// <summary>
    /// The server has already reported the status of the request and does not need to repeat it.
    /// </summary>
    AlreadyReported = 208,

    /// <summary>
    /// The server is returning a response that is the result of applying a delta encoding to the requested resource.
    /// </summary>
    IMUsed = 226,

    /// <summary>
    /// The requested resource has multiple representations and the client should choose one of them.
    /// </summary>
    Ambiguous = 300,

    /// <summary>
    /// The requested resource has multiple representations and the client should choose one of them.
    /// </summary>
    MultipleChoices = 300,

    /// <summary>
    /// The requested resource has been permanently moved to a new location and the client should use the new URI.
    /// </summary>
    Moved = 301,

    /// <summary>
    /// The requested resource has been permanently moved to a new location and the client should use the new URI.
    /// </summary>
    MovedPermanently = 301,

    /// <summary>
    /// The requested resource has been temporarily moved to a new location and the client should use the new URI.
    /// </summary>
    Found = 302,

    /// <summary>
    /// The requested resource has been temporarily moved to a new location and the client should use the new URI.
    /// </summary>
    Redirect = 302,

    /// <summary>
    /// The requested resource can be found at a different URI and the client should use a GET method to retrieve it.
    /// </summary>
    RedirectMethod = 303,

    /// <summary>
    /// The requested resource can be found at a different URI and the client should use a GET method to retrieve it.
    /// </summary>
    SeeOther = 303,

    /// <summary>
    /// The requested resource has not been modified since the last request and the client can use the cached version.
    /// </summary>
    NotModified = 304,

    /// <summary>
    /// The requested resource is only available through a proxy and the client should use the proxy URI.
    /// </summary>
    UseProxy = 305,

    /// <summary>
    /// This status code is no longer used and is reserved for future use.
    /// </summary>
    Unused = 306,

    /// <summary>
    /// The requested resource has been temporarily moved to a new location and the client should use the same method to access it.
    /// </summary>
    RedirectKeepVerb = 307,

    /// <summary>
    /// The requested resource has been temporarily moved to a new location and the client should use the same method to access it.
    /// </summary>
    TemporaryRedirect = 307,

    /// <summary>
    /// The requested resource has been permanently moved to a new location and the client should use the same method to access it.
    /// </summary>
    PermanentRedirect = 308,

    /// <summary>
    /// The server cannot process the request due to a malformed syntax or an invalid parameter.
    /// </summary>
    BadRequest = 400,

    /// <summary>
    /// The request requires authentication and the client should provide valid credentials.
    /// </summary>
    Unauthorized = 401,

    /// <summary>
    /// The request requires payment and the client should provide valid payment information.
    /// </summary>
    PaymentRequired = 402,

    /// <summary>
    /// The server has understood the request, but refuses to authorize it due to insufficient permissions or other reasons.
    /// </summary>
    Forbidden = 403,

    /// <summary>
    /// The server cannot find the requested resource and the client should not repeat the request.
    /// </summary>
    NotFound = 404,

    /// <summary>
    /// The server does not support the method used by the request and the client should use a different method.
    /// </summary>
    MethodNotAllowed = 405,

    /// <summary>
    /// The server cannot produce a response that matches the preferences specified by the request headers.
    /// </summary>
    NotAcceptable = 406,

    /// <summary>
    /// The request requires authentication through a proxy and the client should provide valid proxy credentials.
    /// </summary>
    ProxyAuthenticationRequired = 407,

    /// <summary>
    /// The server did not receive the complete request within the time limit and the client should try again later.
    /// </summary>
    RequestTimeout = 408,

    /// <summary>
    /// The request could not be completed due to a conflict with the current state of the resource.
    /// </summary>
    Conflict = 409,

    /// <summary>
    /// The requested resource is no longer available and the server does not know the new location.
    /// </summary>
    Gone = 410,

    /// <summary>
    /// The request requires a Content-Length header and the client should provide it.
    /// </summary>
    LengthRequired = 411,

    /// <summary>
    /// The request does not meet the preconditions specified by the request headers and the server cannot process it.
    /// </summary>
    PreconditionFailed = 412,

    /// <summary>
    /// The request entity is too large and the server cannot process it.
    /// </summary>
    RequestEntityTooLarge = 413,

    /// <summary>
    /// The request URI is too long and the server cannot process it.
    /// </summary>
    RequestUriTooLong = 414,

    /// <summary>
    /// The request entity has a media type that the server does not support or cannot handle.
    /// </summary>
    UnsupportedMediaType = 415,

    /// <summary>
    /// The request specifies a range that the server cannot satisfy or is invalid.
    /// </summary>
    RequestedRangeNotSatisfiable = 416,

    /// <summary>
    /// The request contains an Expect header that the server cannot meet or is invalid.
    /// </summary>
    ExpectationFailed = 417,

    /// <summary>
    /// The request was directed to a server that is not able to produce a response.
    /// </summary>
    MisdirectedRequest = 421,

    /// <summary>
    /// The request entity is well-formed, but cannot be processed by the server due to semantic errors.
    /// </summary>
    UnprocessableEntity = 422,

    /// <summary>
    /// The requested resource is locked and the client should release it before modifying it.
    /// </summary>
    Locked = 423,

    /// <summary>
    /// The request failed due to a dependency on another request that failed.
    /// </summary>
    FailedDependency = 424,

    /// <summary>
    /// The request requires the server to upgrade to a different protocol and the client should use the Upgrade header to specify it.
    /// </summary>
    UpgradeRequired = 426,

    /// <summary>
    /// The request requires the server to apply preconditions and the client should use the If-Match or If-Unmodified-Since headers to specify them.
    /// </summary>
    PreconditionRequired = 428,

    /// <summary>
    /// The client has sent too many requests in a given time and the server rejects them to prevent overload.
    /// </summary>
    TooManyRequests = 429,

    /// <summary>
    /// The request contains headers that are too large and the server cannot process them.
    /// </summary>
    RequestHeaderFieldsTooLarge = 431,

    /// <summary>
    /// The server is denying access to the requested resource for legal reasons and the client should not repeat the request.
    /// </summary>
    UnavailableForLegalReasons = 451,

    /// <summary>
    /// The server encountered an unexpected error and cannot fulfill the request.
    /// </summary>
    InternalServerError = 500,

    /// <summary>
    /// The server does not support the functionality required by the request and the client should not repeat the request.
    /// </summary>
    NotImplemented = 501,

    /// <summary>
    /// The server received an invalid response from an upstream server and cannot fulfill the request.
    /// </summary>
    BadGateway = 502,

    /// <summary>
    /// The server is temporarily unavailable due to maintenance or overload and the client should try again later.
    /// </summary>
    ServiceUnavailable = 503,

    /// <summary>
    /// The server did not receive a timely response from an upstream server and cannot fulfill the request.
    /// </summary>
    GatewayTimeout = 504,

    /// <summary>
    /// The server does not support the HTTP version used by the request and the client should use a different version.
    /// </summary>
    HttpVersionNotSupported = 505,

    /// <summary>
    /// The server has a configuration error and cannot negotiate a suitable representation for the requested resource.
    /// </summary>
    VariantAlsoNegotiates = 506,

    /// <summary>
    /// The server has insufficient storage space to complete the request.
    /// </summary>
    InsufficientStorage = 507,

    /// <summary>
    /// The server detected an infinite loop while processing the request.
    /// </summary>
    LoopDetected = 508,

    /// <summary>
    /// The request requires additional extensions that the server does not support or cannot handle.
    /// </summary>
    NotExtended = 510,

    /// <summary>
    /// The request requires authentication at the network level and the client should provide valid network credentials.
    /// </summary>
    NetworkAuthenticationRequired = 511,
}
