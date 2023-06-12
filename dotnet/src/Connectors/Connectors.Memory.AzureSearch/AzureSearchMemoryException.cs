// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Memory.AzureSearch;

#pragma warning disable RCS1194 // Implement exception constructors

/// <summary>
/// Exception thrown by the Azure Cognitive Search connector
/// </summary>
public class AzureSearchMemoryException : Exception
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AzureSearchMemoryException"/> class with a provided error code and message.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">The exception message.</param>
    public AzureSearchMemoryException(ErrorCodes errorCode, string? message)
        : this(errorCode, message, innerException: null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureSearchMemoryException"/> class with a provided error code, message, and inner exception.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">A string that describes the error.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public AzureSearchMemoryException(ErrorCodes errorCode, string? message, Exception? innerException)
        : base(GetDefaultMessage(errorCode, message, innerException), innerException)
    {
        this.ErrorCode = errorCode;
    }

    /// <summary>
    /// Gets the error code for this exception.
    /// </summary>
    public ErrorCodes ErrorCode { get; }

    /// <summary>Translate the error code into a default message.</summary>
    private static string GetDefaultMessage(ErrorCodes errorCode, string? message, Exception? innerException)
    {
        if (message is not null) { return message; }

        var description = errorCode.ToString("G");
        return innerException is not null ? $"{description}: {innerException.Message}" : description;
    }

    /// <summary>
    /// Error codes for the Qdrant connector exceptions.
    /// </summary>
    public enum ErrorCodes
    {
        /// <summary>
        /// Unknown error.
        /// </summary>
        UnknownError = -1,

        /// <summary>
        /// Invalid embedding size, the value must be greater than zero
        /// </summary>
        InvalidEmbeddingSize,

        /// <summary>
        /// Invalid index name
        /// </summary>
        InvalidIndexName,

        /// <summary>
        /// Read failure
        /// </summary>
        ReadFailure,

        /// <summary>
        /// Write failure
        /// </summary>
        WriteFailure,
    }
}
