// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Functions.Grpc.Model;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Functions.Grpc.Extensions;

#pragma warning disable RCS1175 // Unused 'this' parameter 'operation'.

/// <summary>
/// Class for extensions methods for the <see cref="GrpcOperation"/> class.
/// </summary>
internal static class GrpcOperationExtensions
{
    /// <summary>
    /// Returns list of gRPC operation parameters.
    /// TODO: not an extension method, `operation` is never used.
    /// </summary>
    /// <returns>The list of parameters.</returns>
    public static IReadOnlyList<KernelParameterMetadata> GetParameters(this GrpcOperation operation)
    {
        var parameters = new KernelParameterMetadata[]
        {
            // Register the "address" parameter so that it's possible to override it if needed.
            new(GrpcOperation.AddressArgumentName)
            {
                Description = "Address for gRPC channel to use.",
            },

            // Register the "payload" parameter to be used as gRPC operation request message.
            new(GrpcOperation.PayloadArgumentName)
            {
                Description = "gRPC request message.",
            },
        };

        return parameters;
    }
}
