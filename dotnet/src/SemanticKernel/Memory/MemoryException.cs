// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Memory logic exception
/// </summary>
public class MemoryException : Exception<MemoryException.ErrorCodes>
{
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

    /// <summary>
    /// Error code.
    /// </summary>
    public ErrorCodes ErrorCode { get; set; }

    /// <summary>
    /// Constructor for MemoryException.
    /// </summary>
    /// <param name="errCode">Error code to put in MemoryException.</param>
    /// <param name="message">Message to put in MemoryException.</param>
    public MemoryException(ErrorCodes errCode, string? message = null) : base(errCode, message)
    {
        this.ErrorCode = errCode;
    }

    /// <summary>
    /// Constructor for MemoryException.
    /// </summary>
    /// <param name="errCode">Error code to put in MemoryException.</param>
    /// <param name="message">Message to put in MemoryException.</param>
    /// <param name="e">Exception to embed in MemoryException.</param>
    public MemoryException(ErrorCodes errCode, string message, Exception? e) : base(errCode, message, e)
    {
        this.ErrorCode = errCode;
    }

    #region private ================================================================================

    private MemoryException()
    {
        // Not allowed, error code is required
    }

    private MemoryException(string message) : base(message)
    {
        // Not allowed, error code is required
    }

    private MemoryException(string message, Exception innerException) : base(message, innerException)
    {
        // Not allowed, error code is required
    }

    #endregion
}
