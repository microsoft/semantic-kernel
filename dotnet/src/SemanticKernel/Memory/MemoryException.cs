// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Kernel logic exception
/// </summary>
public class MemoryException : Exception<MemoryException.ErrorCodes>
{
    /// <summary>
    /// Semantic kernel error codes.
    /// </summary>
    public enum ErrorCodes
    {
        /// <summary>
        /// Unknown error.
        /// </summary>
        UnknownError = -1,

        /// <summary>
        /// Unable to construct memory from serialized metadata.
        /// </summary>
        UnableToDeserializeMetadata,
    }

    /// <summary>
    /// Error code.
    /// </summary>
    public ErrorCodes ErrorCode { get; set; }

    /// <summary>
    /// Constructor for KernelException.
    /// </summary>
    /// <param name="errCode">Error code to put in KernelException.</param>
    /// <param name="message">Message to put in KernelException.</param>
    public MemoryException(ErrorCodes errCode, string? message = null) : base(errCode, message)
    {
        this.ErrorCode = errCode;
    }

    /// <summary>
    /// Constructor for KernelException.
    /// </summary>
    /// <param name="errCode">Error code to put in KernelException.</param>
    /// <param name="message">Message to put in KernelException.</param>
    /// <param name="e">Exception to embed in KernelException.</param>
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
