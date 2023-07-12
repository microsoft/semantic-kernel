// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Services.Diagnostics;

public class PipelineCompletedException : MemoryException
{
    /// <summary>
    /// Initializes a new instance.
    /// </summary>
    public PipelineCompletedException()
        : this(message: null, innerException: null)
    {
    }

    /// <summary>
    /// Initializes a new instance.
    /// </summary>
    /// <param name="message">The exception message.</param>
    public PipelineCompletedException(string? message)
        : this(message, innerException: null)
    {
    }

    /// <summary>
    /// Initializes a new instance.
    /// </summary>
    /// <param name="message">A string that describes the error.</param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public PipelineCompletedException(string? message, Exception? innerException)
        : base(message, innerException)
    {
    }
}
