// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Diagnostics;

#pragma warning disable RCS1194 // Implement exception constructors

/// <summary>
/// Exception thrown for errors related to the Qdrant connector.
/// </summary>
public class QdrantMemoryException : SKException
{
    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantMemoryException"/> class with a provided error code.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    public QdrantMemoryException(ErrorCodes errorCode)
        : this(errorCode, message: null, innerException: null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantMemoryException"/> class with a provided error code and message.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">The exception message.</param>
    public QdrantMemoryException(ErrorCodes errorCode, string? message)
        : this(errorCode, message, innerException: null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantMemoryException"/> class with a provided error code and inner exception.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public QdrantMemoryException(ErrorCodes errorCode, Exception? innerException)
        : this(errorCode, message: null, innerException)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantMemoryException"/> class with a provided error code, message, and inner exception.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">A string that describes the error.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public QdrantMemoryException(ErrorCodes errorCode, string? message, Exception? innerException)
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
        if (message is not null)
        {
            return message;
        }

        string description = errorCode switch
        {
            ErrorCodes.UnableToDeserializeRecordPayload => "Unable to deserialize record payload",
            ErrorCodes.FailedToUpsertVectors => "Failed to upsert vectors",
            ErrorCodes.FailedToGetVectorData => "Failed to get vector data",
            ErrorCodes.FailedToRemoveVectorData => "Failed to remove vector data",
            ErrorCodes.FailedToConvertMemoryRecordToQdrantVectorRecord => "Failed to convert memory record to Qdrant vector record",
            ErrorCodes.FailedToConvertQdrantVectorRecordToMemoryRecord => "Failed to convert Qdrant vector record to memory record",
            _ => $"Unknown error ({errorCode:G})",
        };

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
        /// Failed to deserialize the record payload.
        /// </summary>
        UnableToDeserializeRecordPayload,

        /// <summary>
        /// Failed to upsert the vector.
        /// </summary>
        FailedToUpsertVectors,

        /// <summary>
        /// Failed to get vector data from Qdrant.
        /// </summary>
        FailedToGetVectorData,

        /// <summary>
        /// Failed to remove vector data from Qdrant.
        /// </summary>
        FailedToRemoveVectorData,

        /// <summary>
        /// Failed to convert a memory record to a Qdrant vector record.
        /// </summary>
        FailedToConvertMemoryRecordToQdrantVectorRecord,

        /// <summary>
        /// Failed to convert a Qdrant vector record to a memory record.
        /// </summary>
        FailedToConvertQdrantVectorRecordToMemoryRecord
    }
}
