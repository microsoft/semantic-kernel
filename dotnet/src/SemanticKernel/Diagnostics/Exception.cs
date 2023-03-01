// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Diagnostics;

/// <summary>
/// Base exception for all SK exceptions
/// </summary>
/// <typeparam name="TErrorCode">Enum type used for the error codes</typeparam>
public abstract class Exception<TErrorCode> : Exception where TErrorCode : Enum
{
    /// <summary>
    /// Initializes a new instance of the <see cref="Exception"/> class.
    /// </summary>
    /// <param name="errCode">The error type.</param>
    /// <param name="message">The message.</param>
    protected Exception(TErrorCode errCode, string? message = null) : base(BuildMessage(errCode, message))
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="Exception"/> class.
    /// </summary>
    /// <param name="errCode">The error type.</param>
    /// <param name="message">The message.</param>
    /// <param name="innerException">The inner exception.</param>
    protected Exception(TErrorCode errCode, string? message, Exception? innerException)
        : base(BuildMessage(errCode, message), innerException)
    {
    }

    /// <summary>
    /// Parameterless ctor, do not use
    /// </summary>
    protected Exception()
    {
        // Not allowed, error code is required
    }

    /// <summary>
    /// Standard ctor, do not use
    /// </summary>
    /// <param name="message">Exception message</param>
    protected Exception(string message) : base(message)
    {
        // Not allowed, error code is required
    }

    /// <summary>
    /// Standard ctor, do not use
    /// </summary>
    /// <param name="message">Exception message</param>
    /// <param name="innerException">Internal exception</param>
    protected Exception(string message, Exception innerException) : base(message, innerException)
    {
        // Not allowed, error code is required
    }

    private static string BuildMessage(TErrorCode errorType, string? message)
    {
        return message != null ? $"{errorType.ToString("G")}: {message}" : errorType.ToString("G");
    }
}
