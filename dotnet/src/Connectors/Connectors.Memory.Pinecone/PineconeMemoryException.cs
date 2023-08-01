// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone;

#pragma warning disable CA1032 // Implement standard exception constructors

/// <summary>
/// Custom exceptions for the Pinecone connector.
/// </summary>
public class PineconeMemoryException : SKException
{
    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeMemoryException"/> class with a provided error code and message.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">The exception message.</param>
    public PineconeMemoryException(ErrorCodes errorCode, string? message)
        : this(errorCode: errorCode, message: message, innerException: null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeMemoryException"/> class with a provided error code and inner exception.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public PineconeMemoryException(ErrorCodes errorCode, Exception? innerException)
        : this(errorCode: errorCode, message: null, innerException: innerException)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeMemoryException"/> class with a provided error code, message, and inner exception.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">A string that describes the error.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public PineconeMemoryException(ErrorCodes errorCode, string? message = null, Exception? innerException = null)
        : base(message: GetDefaultMessage(errorCode: errorCode, message: message, innerException: innerException), innerException: innerException)
    {
        this.ErrorCode = errorCode;
    }

    protected PineconeMemoryException() : base()
    {
    }

    protected PineconeMemoryException(string? message) : base(message)
    {
    }

    protected PineconeMemoryException(string? message, Exception? innerException) : base(message, innerException)
    {
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
            ErrorCodes.UnableToDeserializeDocumentMetadata => "Unable to deserialize document metadata",
            ErrorCodes.FailedToUpsertVectors => "Failed to upsert vectors",
            ErrorCodes.FailedToGetVectorData => "Failed to get vector data",
            ErrorCodes.FailedToRemoveVectorData => "Failed to remove vector data",
            ErrorCodes.FailedToConvertMemoryRecordToPineconeDocument => "Failed to convert memory record to Pinecone document",
            ErrorCodes.FailedToConvertPineconeDocumentToMemoryRecord => "Failed to convert Pinecone document record to memory record",
            _ => $"Unknown error ({errorCode:G})"
        };

        return innerException is not null ? $"{description}: {innerException.Message}" : description;
    }

    /// <summary>
    /// Error codes for the Pinecone connector exceptions.
    /// </summary>
    public enum ErrorCodes
    {
        /// <summary>
        /// Unknown error.
        /// </summary>
        UnknownError,

        /// <summary>
        /// The index is not found.
        /// </summary>
        IndexNotFound,

        /// <summary>
        /// The index is not ready.
        /// </summary>
        IndexNotReady,

        /// <summary>
        /// The index host is unknown.
        /// </summary>
        UnknownIndexHost,

        /// <summary>
        /// Failed to deserialize the record payload.
        /// </summary>
        UnableToDeserializeDocumentMetadata,

        /// <summary>
        /// Failed to upsert the vector.
        /// </summary>
        FailedToUpsertVectors,

        /// <summary>
        /// Failed to get vector data from Pinecone.
        /// </summary>
        FailedToGetVectorData,

        /// <summary>
        /// Failed to remove vector data from Pinecone.
        /// </summary>
        FailedToRemoveVectorData,

        /// <summary>
        /// Failed to convert a memory record to a Pinecone vector record.
        /// </summary>
        FailedToConvertMemoryRecordToPineconeDocument,

        /// <summary>
        /// Failed to convert a Pinecone vector record to a memory record.
        /// </summary>
        FailedToConvertPineconeDocumentToMemoryRecord
    }
}
