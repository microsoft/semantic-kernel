// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Diagnostics;

#pragma warning disable CA1032 // Implement standard exception constructors

/// <summary>
/// Exception thrown for errors related to validation.
/// </summary>
public class ValidationException : SKException
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ValidationException"/> class with a provided error code.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    public ValidationException(ErrorCodes errorCode)
        : this(errorCode, message: null, innerException: null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ValidationException"/> class with a provided error code and message.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">The exception message.</param>
    public ValidationException(ErrorCodes errorCode, string? message)
        : this(errorCode, message, innerException: null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ValidationException"/> class with a provided error code, message, and inner exception.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">A string that describes the error.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public ValidationException(ErrorCodes errorCode, string? message, Exception? innerException)
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
            ErrorCodes.NullValue => "Null value",
            ErrorCodes.EmptyValue => "Empty value",
            ErrorCodes.OutOfRange => "Out of range",
            ErrorCodes.MissingPrefix => "Missing prefix",
            ErrorCodes.DirectoryNotFound => "Directory not found",
            _ => $"Unknown error ({errorCode:G})",
        };

        return message is not null ? $"{description}: {message}" : description;
    }

    /// <summary>
    /// Error codes for <see cref="ValidationException"/>.
    /// </summary>
    public enum ErrorCodes
    {
        /// <summary>
        /// Unknown error.
        /// </summary>
        UnknownError = -1,

        /// <summary>
        /// Null value.
        /// </summary>
        NullValue,

        /// <summary>
        /// Empty value.
        /// </summary>
        EmptyValue,

        /// <summary>
        /// Out of range.
        /// </summary>
        OutOfRange,

        /// <summary>
        /// Missing prefix.
        /// </summary>
        MissingPrefix,

        /// <summary>
        /// Directory not found.
        /// </summary>
        DirectoryNotFound,
    }
}
