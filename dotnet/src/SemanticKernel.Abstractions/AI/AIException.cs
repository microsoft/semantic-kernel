// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.AI;

#pragma warning disable RCS1194 // Implement exception constructors

/// <summary>
/// Exception thrown for errors related to AI logic.
/// </summary>
public class AIException : SKException
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AIException"/> class with a provided error code and message.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">The exception message.</param>
    public AIException(ErrorCodes errorCode, string? message)
        : this(errorCode, message, detail: null, innerException: null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AIException"/> class with a provided error code, message, and inner exception.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">A string that describes the error.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public AIException(ErrorCodes errorCode, string? message, Exception? innerException)
        : this(errorCode, message, detail: null, innerException)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AIException"/> class with a provided error code, message, and inner exception.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">A string that describes the error.</param>
    /// <param name="detail">A string that provides additional details about the error.</param>
    public AIException(ErrorCodes errorCode, string? message, string? detail)
        : this(errorCode, message, detail, innerException: null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AIException"/> class with a provided error code, message, additional details, and inner exception.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">A string that describes the error.</param>
    /// <param name="detail">A string that provides additional details about the error.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public AIException(ErrorCodes errorCode, string? message = null, string? detail = null, Exception? innerException = null)
        : base(GetDefaultMessage(errorCode, message), innerException)
    {
        this.ErrorCode = errorCode;
        this.Detail = detail;
    }

    /// <summary>
    /// Gets the error code for this exception.
    /// </summary>
    public ErrorCodes ErrorCode { get; }

    /// <summary>
    /// Gets the extended details for this exception.
    /// </summary>
    public string? Detail { get; }

    /// <summary>Translate the error code into a default message.</summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="defaultMessage">Default error message if nothing available.</param>
    private static string GetDefaultMessage(ErrorCodes errorCode, string? defaultMessage)
    {
        string description = errorCode switch
        {
            ErrorCodes.AccessDenied => "Access denied",
            ErrorCodes.InvalidRequest => "Invalid request",
            ErrorCodes.Throttling => "Throttling",
            ErrorCodes.RequestTimeout => "Request timeout",
            ErrorCodes.ServiceError => "Service error",
            _ => $"Unknown error ({errorCode:G})",
        };

        return defaultMessage is not null ? $"{description}: {defaultMessage}" : description;
    }

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
        /// Access is denied.
        /// </summary>
        AccessDenied,

        /// <summary>
        /// The request was invalid.
        /// </summary>
        InvalidRequest,

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
    }
}
