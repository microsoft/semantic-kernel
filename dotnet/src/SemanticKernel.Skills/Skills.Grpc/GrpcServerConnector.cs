// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Grpc.Core;
using Grpc.Net.Client;

namespace Microsoft.SemanticKernel.Skills.Grpc;

/// <summary>
/// Provides a concrete implementation of the IGrpcInvoker interface.
/// </summary>
public class GrpcServerConnector : IGrpcServerConnector
{
    /// <inheritdoc cref="IGrpcServerConnector" />
    public async Task<TResponse> InvokeAsync<TRequest, TResponse>(
        Func<GrpcChannel, TRequest, CallOptions, Task<TResponse>> method,
        TRequest request,
        string serverAddress,
        CallOptions? callOptions = null)
        where TRequest : class
        where TResponse : class
    {
        using var channel = GrpcChannel.ForAddress(serverAddress);

        callOptions ??= new CallOptions();

        return await method(channel, request, callOptions.Value);
    }
}
