// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Grpc.Core;
using Grpc.Net.Client;

namespace Microsoft.SemanticKernel.Skills.Grpc;

/// <summary>
/// Defines a generic gRPC invoker interface for making gRPC calls.
/// </summary>
public interface IGrpcServerConnector
{
    /// <summary>
    /// Invokes a gRPC method asynchronously.
    /// </summary>
    /// <typeparam name="TRequest">The type of the gRPC request.</typeparam>
    /// <typeparam name="TResponse">The type of the gRPC response.</typeparam>
    /// <param name="method">The gRPC method to invoke.</param>
    /// <param name="request">The gRPC request object.</param>
    /// <param name="serverAddress">The address of the gRPC server.</param>
    /// <param name="callOptions">Optional call options for the gRPC method.</param>
    /// <returns>A task representing the asynchronous operation with the result of type TResponse.</returns>
    Task<TResponse> InvokeAsync<TRequest, TResponse>(
        Func<GrpcChannel, TRequest, CallOptions, Task<TResponse>> method,
        TRequest request,
        string serverAddress,
        CallOptions? callOptions = null)
        where TRequest : class
        where TResponse : class;
}
