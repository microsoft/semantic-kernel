// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai; // Copyright (c) Microsoft. All rights reserved.

/** AI logic exception */
public class AIException extends RuntimeException {
    /*
    /// <summary>
    /// Possible error codes for exceptions
    /// </summary>
    public enum ErrorCodes
    {
        /// <summary>
        /// Unknown error.
        /// </summary>
        UnknownError = -1,

        /// <summary>
        /// No response.
        /// </summary>
        NoResponse,

        /// <summary>
        /// Access is denied.
        /// </summary>
        AccessDenied,

        /// <summary>
        /// The request was invalid.
        /// </summary>
        InvalidRequest,

        /// <summary>
        /// The content of the response was invalid.
        /// </summary>
        InvalidResponseContent,

        /// <summary>
        /// The request was throttled.
        /// </summary>
        Throttling,

        /// <summary>
        /// The request timed out.
        /// </summary>
        RequestTimeout,

        /// <summary>
        /// There was an error in the service.
        /// </summary>
        ServiceError,

        /// <summary>
        /// The requested model is not available.
        /// </summary>
        ModelNotAvailable,

        /// <summary>
        /// The supplied configuration was invalid.
        /// </summary>
        InvalidConfiguration,

        /// <summary>
        /// The function is not supported.
        /// </summary>
        FunctionTypeNotSupported,
    }

    /// <summary>
    /// The exception's error code.
    /// </summary>
    public ErrorCodes ErrorCode { get; set; }

    /// <summary>
    /// The exception's detail.
    /// </summary>
    public string? Detail { get; set; }

    /// <summary>
    /// Construct an exception with an error code and message.
    /// </summary>
    /// <param name="errCode">Error code of the exception.</param>
    /// <param name="message">Message of the exception</param>
    public AIException(ErrorCodes errCode, string? message = null) : base(errCode, message)
    {
        this.ErrorCode = errCode;
    }

    /// <summary>
    /// Construct an exception with an error code, message, and existing exception.
    /// </summary>
    /// <param name="errCode">Error code of the exception.</param>
    /// <param name="message">Message of the exception.</param>
    /// <param name="e">An exception that was thrown.</param>
    public AIException(ErrorCodes errCode, string message, Exception? e) : base(errCode, message, e)
    {
        this.ErrorCode = errCode;
    }

    /// <summary>
    /// Construct an exception with an error code, message, and existing exception.
    /// </summary>
    /// <param name="errCode">Error code of the exception.</param>
    /// <param name="message">Message of the exception.</param>
    /// <param name="detail">More details about the exception</param>
    public AIException(ErrorCodes errCode, string message, string? detail) : this(errCode, message)
    {
        this.Detail = detail;
    }

    #region private ================================================================================

    private AIException()
    {
        // Not allowed, error code is required
    }

    private AIException(string message) : base(message)
    {
        // Not allowed, error code is required
    }

    private AIException(string message, Exception innerException) : base(message, innerException)
    {
        // Not allowed, error code is required
    }

    #endregion

     */
}
