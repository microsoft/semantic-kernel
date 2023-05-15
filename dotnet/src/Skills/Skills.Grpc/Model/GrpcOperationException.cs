// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Skills.Grpc.Model;

/// <summary>
/// Exception to be throw if a gRPC operation has failed.
/// </summary>
public class GrpcOperationException : Exception
{
    /// <summary>
    /// Creates an instance of a <see cref="GrpcOperationException"/> class.
    /// </summary>
    /// <param name="message">The exception message.</param>
    internal GrpcOperationException(string message) : base(message)
    {
    }

    /// <summary>
    /// Creates an instance of a <see cref="GrpcOperationException"/> class.
    /// </summary>
    /// <param name="message">The exception message.</param>
    /// <param name="innerException">The inner exception.</param>
    internal GrpcOperationException(string message, Exception innerException) : base(message, innerException)
    {
    }

    /// <summary>
    /// Creates an instance of a <see cref="GrpcOperationException"/> class.
    /// </summary>
    internal GrpcOperationException()
    {
    }
}
