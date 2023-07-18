// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Memory;

#pragma warning disable RCS1194 // Implement exception constructors

/// <summary>
/// Exception thrown for errors related to memory logic.
/// </summary>
public class MemoryException : SKException
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MemoryException"/> class with a provided error code and message.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">The exception message.</param>
    public MemoryException(ErrorCodes errorCode, string? message)
        : this(errorCode, message, innerException: null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="MemoryException"/> class with a provided error code, message, and inner exception.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">A string that describes the error.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public MemoryException(ErrorCodes errorCode, string? message = null, Exception? innerException = null)
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
            ErrorCodes.FailedToCreateCollection => "Failed to create collection",
            ErrorCodes.FailedToDeleteCollection => "Failed to delete collection",
            ErrorCodes.UnableToDeserializeMetadata => "Unable to deserialize metadata",
            ErrorCodes.AttemptedToAccessNonexistentCollection => "Attempted to access non-existent collection",
            _ => $"Unknown error ({errorCode:G})",
        };

        return message is not null ? $"{description}: {message}" : description;
    }

    /// <summary>
    /// Semantic kernel memory error codes.
    /// </summary>
    public enum ErrorCodes
    {
        /// <summary>
        /// Unknown error.
        /// </summary>
        UnknownError = -1,

        /// <summary>
        /// Failed to create collection.
        /// </summary>
        FailedToCreateCollection,

        /// <summary>
        /// Failed to delete collection.
        /// </summary>
        FailedToDeleteCollection,

        /// <summary>
        /// Unable to construct memory from serialized metadata.
        /// </summary>
        UnableToDeserializeMetadata,

        /// <summary>
        /// Attempted to access a memory collection that does not exist.
        /// </summary>
        AttemptedToAccessNonexistentCollection,
    }
}
