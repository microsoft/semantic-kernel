// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Reliability.Basic;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of KernelConfig
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides extension methods for the <see cref="KernelBuilder"/>.
/// </summary>
public static class ReliabilityBasicKernelBuilderExtensions
{
    /// <summary>
    /// Sets the default retry configuration for any kernel http request.
    /// </summary>
    /// <param name="builder">Target instance</param>
    /// <param name="retryConfig">Retry configuration</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithRetryBasic(this KernelBuilder builder,
        BasicRetryConfig retryConfig)
    {
        var httpHandlerFactory = new BasicHttpRetryHandlerFactory(retryConfig);

        return builder.WithHttpHandlerFactory(httpHandlerFactory);
    }
}
