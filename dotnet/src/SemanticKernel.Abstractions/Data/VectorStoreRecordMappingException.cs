// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Exception thrown when a failure occurs while trying to convert models for storage or retrieval.
/// </summary>
[Experimental("SKEXP0001")]
public class VectorStoreRecordMappingException : VectorStoreException
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordMappingException"/> class.
    /// </summary>
    public VectorStoreRecordMappingException()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordMappingException"/> class with a specified error message.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    public VectorStoreRecordMappingException(string? message) : base(message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordMappingException"/> class with a specified error message and a reference to the inner exception that is the cause of this exception.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    /// <param name="innerException">The exception that is the cause of the current exception, or a null reference if no inner exception is specified.</param>
    public VectorStoreRecordMappingException(string? message, Exception? innerException) : base(message, innerException)
    {
    }
}
