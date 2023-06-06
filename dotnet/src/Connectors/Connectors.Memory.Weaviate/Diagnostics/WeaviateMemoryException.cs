// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Diagnostics;

#pragma warning disable RCS1194 // Implement exception constructors

/// <summary>
/// Exception thrown for errors related to the Weaviate connector.
/// </summary>
public class WeaviateMemoryException : SKException
{
    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateMemoryException"/> class with a provided error code.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    public WeaviateMemoryException(ErrorCodes errorCode)
        : this(errorCode, message: null, innerException: null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateMemoryException"/> class with a provided error code and message.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">The exception message.</param>
    public WeaviateMemoryException(ErrorCodes errorCode, string? message)
        : this(errorCode, message, innerException: null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateMemoryException"/> class with a provided error code and inner exception.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public WeaviateMemoryException(ErrorCodes errorCode, Exception? innerException)
        : this(errorCode, message: null, innerException)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateMemoryException"/> class with a provided error code, message, and inner exception.
    /// </summary>
    /// <param name="errorCode">The error code.</param>
    /// <param name="message">A string that describes the error.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public WeaviateMemoryException(ErrorCodes errorCode, string? message, Exception? innerException)
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
            ErrorCodes.FailedToUpsertVectors => "Failed to upsert vectors",
            ErrorCodes.FailedToGetVectorData => "Failed to get vector data",
            ErrorCodes.FailedToRemoveVectorData => "Failed to remove vector data",
            ErrorCodes.CollectionNameConflict => "Naming conflict for the collection name",
            ErrorCodes.FailedToCreateCollection => "Failed to create the collection",
            ErrorCodes.FailedToDeleteCollection => "Failed to delete the collection",
            ErrorCodes.FailedToListCollections => "Failed to list collections",
            ErrorCodes.FailedToGetClass => "Failed to get class",
            _ => $"Unknown error ({errorCode:G})",
        };

        return innerException is not null ? $"{description}: {innerException.Message}" : description;
    }

    /// <summary>
    /// Error codes for the Weaviate connector exceptions.
    /// </summary>
    public enum ErrorCodes
    {
        /// <summary>
        ///     Failed to upsert the vector.
        /// </summary>
        FailedToUpsertVectors,

        /// <summary>
        ///     Failed to get vector data from Weaviate.
        /// </summary>
        FailedToGetVectorData,

        /// <summary>
        ///     Failed to remove vector data from Weaviate.
        /// </summary>
        FailedToRemoveVectorData,

        /// <summary>
        ///     Failed to create a collection.
        /// </summary>
        FailedToCreateCollection,

        // ReSharper disable once CommentTypo
        /// <summary>
        ///     Naming conflict for the collection name.
        ///     For example a collectionName of '__this_collection' and 'this_collection' are
        ///     both transformed to the class name of SKthiscollection - even though
        ///     semantic kernel would consider them as unique collection names.
        /// </summary>
        CollectionNameConflict,

        /// <summary>
        ///     Failed to delete a collection.
        /// </summary>
        FailedToDeleteCollection,

        /// <summary>
        ///     Failed to list collections.
        /// </summary>
        FailedToListCollections,

        /// <summary>
        ///     Failed to get a Weaviate class.
        /// </summary>
        FailedToGetClass
    }
}
