// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Diagnostics;

/// <summary>
/// Custom exceptions for the Qdrant connector.
/// </summary>
public class QdrantMemoryException : Exception<QdrantMemoryException.ErrorCodes>
{
    /// <summary>
    /// Error codes for the Qdrant connector exceptions.
    /// </summary>
    public enum ErrorCodes
    {
        /// <summary>
        /// Unknown error.
        /// </summary>
        UnknownError,

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

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantMemoryException"/> class with error code unknown.
    /// </summary>
    /// <param name="message">The exception message.</param>
    public QdrantMemoryException(string message)
        : this(ErrorCodes.UnknownError, message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantMemoryException"/> class with a provided error code.
    /// </summary>
    /// <param name="error">The error code.</param>
    /// <param name="message">The exception message.</param>
    public QdrantMemoryException(ErrorCodes error, string message)
        : base(error, message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantMemoryException"/> class with an inner exception.
    /// </summary>
    /// <param name="error">The error code.</param>
    /// <param name="message">The exception message.</param>
    /// <param name="innerException">The inner exception</param>
    public QdrantMemoryException(ErrorCodes error, string message, Exception innerException)
        : base(BuildMessage(error, message), innerException)
    {
    }

    private QdrantMemoryException()
    {
    }

    private static string BuildMessage(ErrorCodes error, string? message)
    {
        return message != null ? $"{error.ToString("G")}: {message}" : error.ToString("G");
    }

    private QdrantMemoryException(string message, System.Exception innerException) : base(message, innerException)
    {
    }
}
