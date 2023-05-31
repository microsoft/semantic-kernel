// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Security;

#pragma warning disable RCS1194 // Implement standard exception constructors

/// <summary>
/// Untrusted content exception, used to warn about:
/// - untrusted content in the context passed to any function
/// - untrusted prompts when using semantic functions
/// </summary>
public class UntrustedContentException : SKException
{
    /// <summary>
    /// Initializes a new instance of the <see cref="UntrustedContentException"/> class with a provided error code.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    public UntrustedContentException(ErrorCodes errorCode)
        : this(errorCode, message: null, innerException: null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="UntrustedContentException"/> class with a provided error code and message.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">The exception message.</param>
    public UntrustedContentException(ErrorCodes errorCode, string? message)
        : this(errorCode, message, innerException: null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="UntrustedContentException"/> class with a provided error code, message, and inner exception.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">A string that describes the error.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public UntrustedContentException(ErrorCodes errorCode, string? message, Exception? innerException)
        : base(GetDefaultMessage(errorCode, message), innerException)
    {
        this.ErrorCode = errorCode;
    }

    /// <summary>
    /// Gets the error code for this exception.
    /// </summary>
    public ErrorCodes ErrorCode { get; }

    /// <summary>Translate the error code into a default message.</summary>
    private static string GetDefaultMessage(ErrorCodes errorCode, string? message)
    {
        string description = errorCode switch
        {
            ErrorCodes.SensitiveFunctionWithUntrustedContent => "Sensitive function with untrusted content",
            _ => $"Unknown error ({errorCode:G})",
        };

        return message is not null ? $"{description}: {message}" : description;
    }

    /// <summary>
    /// Error codes for <see cref="UntrustedContentException"/>.
    /// </summary>
    public enum ErrorCodes
    {
        /// <summary>
        /// Unknown error.
        /// </summary>
        UnknownError = -1,

        /// <summary>
        /// Sensitive function was called with untrusted content.
        /// </summary>
        SensitiveFunctionWithUntrustedContent,
    }
}
