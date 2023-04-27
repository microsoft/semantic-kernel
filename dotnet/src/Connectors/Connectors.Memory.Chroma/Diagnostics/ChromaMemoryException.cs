// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma.Diagnostics;

/// <summary>
/// Custom exceptions for the Chroma connector.
/// </summary>
public class ChromaMemoryException : Exception<ChromaMemoryException.ErrorCodes>
{
    /// <summary>
    /// Error codes for the Chroma connector exceptions.
    /// </summary>
    public enum ErrorCodes
    {
        /// <summary>
        /// Unknown error.
        /// </summary>
        UnknownError,

        /// <summary>
        /// Failed to get vector/points data from Chroma.
        /// </summary>
        NoDatapointsException,

        /// <summary>
        /// No Index found from Chroma.
        /// </summary>
        NoIndexException,

        /// <summary>
        /// Invalid Dimension in Chroma.
        /// </summary>
        InvalidDimensionException,

        /// <summary>
        /// Not Enough Elements in Chroma.
        /// </summary>
        NotEnoughElementsException,

        /// <summary>
        /// Failed to deserialize the record payload.
        /// </summary>
        UnableToDeserializeRecordPayload,

        /// <summary>
        /// Failed to upsert the vector.
        /// </summary>
        FailedToUpsertVectors,


        /// <summary>
        /// Failed to remove vector data from Chroma.
        /// </summary>
        FailedToRemoveVectorData,

        /// <summary>
        /// Failed to convert a memory record to a Chroma vector record.
        /// </summary>
        FailedToConvertMemoryRecordToChromaVectorRecord,

        /// <summary>
        /// Failed to convert a Chroma vector record to a memory record.
        /// </summary>
        FailedToConvertChromaVectorRecordToMemoryRecord
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChromaMemoryException"/> class with error code unknown.
    /// </summary>
    /// <param name="message">The exception message.</param>
    public ChromaMemoryException(string message)
        : this(ErrorCodes.UnknownError, message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChromaMemoryException"/> class with a provided error code.
    /// </summary>
    /// <param name="error">The error code.</param>
    /// <param name="message">The exception message.</param>
    public ChromaMemoryException(ErrorCodes error, string message)
        : base(error, message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChromaMemoryException"/> class with an inner exception.
    /// </summary>
    /// <param name="error">The error code.</param>
    /// <param name="message">The exception message.</param>
    /// <param name="innerException">The inner exception</param>
    public ChromaMemoryException(ErrorCodes error, string message, Exception innerException)
        : base(BuildMessage(error, message), innerException)
    {
    }

    private ChromaMemoryException()
    {
    }

    private static string BuildMessage(ErrorCodes error, string? message)
    {
        return message != null ? $"{error.ToString("G")}: {message}" : error.ToString("G");
    }

    private ChromaMemoryException(string message, System.Exception innerException) : base(message, innerException)
    {
    }
}
