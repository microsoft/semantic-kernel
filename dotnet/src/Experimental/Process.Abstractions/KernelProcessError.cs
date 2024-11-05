// Copyright (c) Microsoft. All rights reserved.
using System;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents an failure that occurred during the execution of a process.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="KernelProcessError"/> class.
/// </remarks>
public sealed record KernelProcessError
{
    /// <summary>
    ///The exception type name.
    /// </summary>
    public string Type { get; init; } = string.Empty;

    /// <summary>
    /// The exception message (<see cref="Exception.Message"/>.
    /// </summary>
    public string Message { get; init; } = string.Empty;

    /// <summary>
    /// The exception stack-trace (<see cref="Exception.StackTrace"/>.
    /// </summary>
    public string? StackTrace { get; init; }

    /// <summary>
    /// The inner failure, when exists, as <see cref="KernelProcessError"/>.
    /// </summary>
    public KernelProcessError? InnerError { get; init; }

    /// <summary>
    /// Factory method to create a <see cref="KernelProcessError"/> from a source <see cref="Exception"/> object.
    /// </summary>
    public static KernelProcessError FromException(Exception ex) =>
        new()
        {
            Type = ex.GetType().Name,
            Message = ex.Message,
            StackTrace = ex.StackTrace,
            InnerError = ex.InnerException is not null ? FromException(ex.InnerException) : null
        };
}
