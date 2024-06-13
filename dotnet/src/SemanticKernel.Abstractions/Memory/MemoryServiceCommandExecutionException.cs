// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Exception thrown when a memory service command fails, such as upserting a record or deleting a collection.
/// </summary>
public class MemoryServiceCommandExecutionException : KernelException
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MemoryServiceCommandExecutionException"/> class.
    /// </summary>
    public MemoryServiceCommandExecutionException()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="MemoryServiceCommandExecutionException"/> class with a specified error message.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    public MemoryServiceCommandExecutionException(string? message) : base(message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="MemoryServiceCommandExecutionException"/> class with a specified error message and a reference to the inner exception that is the cause of this exception.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    /// <param name="innerException">The exception that is the cause of the current exception, or a null reference if no inner exception is specified.</param>
    public MemoryServiceCommandExecutionException(string? message, Exception? innerException) : base(message, innerException)
    {
    }
}
