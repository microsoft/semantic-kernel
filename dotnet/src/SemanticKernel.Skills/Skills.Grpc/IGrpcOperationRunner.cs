// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Skills.Grpc.Model;

namespace Skills.Grpc;

/// <summary>
/// Interface for gRPC operation runner classes.
/// </summary>
internal interface IGrpcOperationRunner
{
    /// <summary>
    /// Runs a gRPC operation.
    /// </summary>
    /// <param name="operation">The operation to run.</param>
    /// <param name="arguments">The operation arguments.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The result of the operation run.</returns>
    Task<object> RunAsync(GrpcOperation operation, IDictionary<string, string> arguments, CancellationToken cancellationToken = default);
}
