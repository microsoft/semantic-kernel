// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Functions.Grpc.Model;
using Microsoft.SemanticKernel.SkillDefinition;

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
    public static IReadOnlyList<ParameterView> GetParameters(this GrpcOperation operation)
    {
        var parameters = new ParameterView[]
        {
            // Register the "address" parameter so that it's possible to override it if needed.
            new ParameterView(GrpcOperation.AddressArgumentName,
                "Address for gRPC channel to use.",
                string.Empty),

            // Register the "payload" parameter to be used as gRPC operation request message.
            new ParameterView(GrpcOperation.PayloadArgumentName,
                "gRPC request message.",
                string.Empty)
        };

        return parameters;
    }
}
