// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Diagnostics;

/// <summary>
/// Generic validation exception
/// </summary>
public class ValidationException : Exception<ValidationException.ErrorCodes>
{
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

    /// <summary>
    /// Gets the error code of the exception.
    /// </summary>
    public ErrorCodes ErrorCode { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="ValidationException"/> class.
    /// </summary>
    /// <param name="errCode">The error code.</param>
    /// <param name="message">The message.</param>
    public ValidationException(ErrorCodes errCode, string? message = null) : base(errCode, message)
    {
        this.ErrorCode = errCode;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ValidationException"/> class.
    /// </summary>
    /// <param name="errCode">The error code.</param>
    /// <param name="message">The message.</param>
    /// <param name="e">The inner exception.</param>
    public ValidationException(ErrorCodes errCode, string message, Exception? e) : base(errCode, message, e)
    {
        this.ErrorCode = errCode;
    }

    #region private ================================================================================

    private ValidationException()
    {
        // Not allowed, error code is required
    }

    private ValidationException(string message) : base(message)
    {
        // Not allowed, error code is required
    }

    private ValidationException(string message, Exception innerException) : base(message, innerException)
    {
        // Not allowed, error code is required
    }

    #endregion
}
