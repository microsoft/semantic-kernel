// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents an failure that occurred during the execution of a process.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="KernelProcessError"/> class.
/// </remarks>
/// <param name="Type">The exception type name</param>
/// <param name="Message">The exception message (<see cref="Exception.Message"/></param>
/// <param name="StackTrace">The exception stack-trace (<see cref="Exception.StackTrace"/></param>
[DataContract]
public sealed record KernelProcessError(
    [property:DataMember]
    string Type,
    [property:DataMember]
    string Message,
    [property:DataMember]
    string? StackTrace)
{
    /// <summary>
    /// The inner failure, when exists, as <see cref="KernelProcessError"/>.
    /// </summary>
    [DataMember]
    public KernelProcessError? InnerError { get; init; }

    /// <summary>
    /// Factory method to create a <see cref="KernelProcessError"/> from a source <see cref="Exception"/> object.
    /// </summary>
    public static KernelProcessError FromException(Exception ex) =>
        new(ex.GetType().Name, ex.Message, ex.StackTrace)
        {
            InnerError = ex.InnerException is not null ? FromException(ex.InnerException) : null
        };
}
