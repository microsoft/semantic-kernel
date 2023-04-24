using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone;

/// <summary>
/// Custom exceptions for the Qdrant connector.
/// </summary>
public class PineconeMemoryException : Exception<PineconeMemoryException.ErrorCodes>
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
        /// The index is not ready.
        /// </summary>
        IndexNotReady,

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
        FailedToConvertMemoryRecordToPineconeDocument,

        /// <summary>
        /// Failed to convert a Qdrant vector record to a memory record.
        /// </summary>
        FailedToConvertPineconeDocumentToMemoryRecord
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeMemoryException"/> class with error code unknown.
    /// </summary>
    /// <param name="message">The exception message.</param>
    public PineconeMemoryException(string message)
        : this(ErrorCodes.UnknownError, message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeMemoryException"/> class with a provided error code.
    /// </summary>
    /// <param name="error">The error code.</param>
    /// <param name="message">The exception message.</param>
    public PineconeMemoryException(ErrorCodes error, string message)
        : base(error, message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeMemoryException"/> class with an inner exception.
    /// </summary>
    /// <param name="error">The error code.</param>
    /// <param name="message">The exception message.</param>
    /// <param name="innerException">The inner exception</param>
    public PineconeMemoryException(ErrorCodes error, string message, Exception innerException)
        : base(BuildMessage(error, message), innerException)
    {
    }

    private PineconeMemoryException()
    {
    }

    private static string BuildMessage(ErrorCodes error, string? message)
    {
        return message != null ? $"{error.ToString("G")}: {message}" : error.ToString("G");
    }

    private PineconeMemoryException(string message, Exception innerException) : base(message, innerException)
    {
    }
}
