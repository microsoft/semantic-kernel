// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents an exception specific to HTTP operations.
/// </summary>
/// <remarks>
/// Instances of this class optionally contain telemetry information in the Exception.Data property using keys that are consistent with the OpenTelemetry standard.
/// See https://opentelemetry.io/ for more information.
/// </remarks>
public class HttpOperationException : Exception
{
    /// <summary>
    /// Initializes a new instance of the <see cref="HttpOperationException"/> class.
    /// </summary>
    public HttpOperationException()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HttpOperationException"/> class with its message set to <paramref name="message"/>.
    /// </summary>
    /// <param name="message">A string that describes the error.</param>
    public HttpOperationException(string? message) : base(message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HttpOperationException"/> class with its message set to <paramref name="message"/>.
    /// </summary>
    /// <param name="message">A string that describes the error.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public HttpOperationException(string? message, Exception? innerException) : base(message, innerException)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HttpOperationException"/> class with its message
    /// and additional properties for the HTTP status code and response content.
    /// </summary>
    /// <param name="statusCode">The HTTP status code.</param>
    /// <param name="responseContent">The content of the HTTP response.</param>
    /// <param name="message">A string that describes the error.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public HttpOperationException(HttpStatusCode? statusCode, string? responseContent, string? message, Exception? innerException)
        : base(message, innerException)
    {
        this.StatusCode = statusCode;
        this.ResponseContent = responseContent;
    }

    /// <summary>
    /// Gets or sets the HTTP status code. If the property is null, it indicates that no response was received.
    /// </summary>
    public HttpStatusCode? StatusCode { get; set; }

    /// <summary>
    /// Gets or sets the content of the HTTP response.
    /// </summary>
    public string? ResponseContent { get; set; }

    /// <summary>
    /// Gets the method used for the HTTP request.
    /// </summary>
    /// <remarks>
    /// This information is only available in limited circumstances e.g. when using Open API plugins.
    /// </remarks>
    [Obsolete("This property is obsolete and will be removed in a future version. Use the Exception.Data['Name'] instead.")]
    public string? RequestMethod { get; set; }

    /// <summary>
    /// Gets the System.Uri used for the HTTP request.
    /// </summary>
    /// <remarks>
    /// This information is only available in limited circumstances e.g. when using Open API plugins.
    /// </remarks>
    [Obsolete("This property is obsolete and will be removed in a future version. Use the Exception.Data['Url'] instead.")]
    public Uri? RequestUri { get; set; }

    /// <summary>
    /// Gets the payload sent in the request.
    /// </summary>
    /// <remarks>
    /// This information is only available in limited circumstances e.g. when using Open API plugins.
    /// </remarks>
    [Obsolete("This property is obsolete and will be removed in a future version. Use the Exception.Data['Data'] instead.")]
    public object? RequestPayload { get; set; }
}
