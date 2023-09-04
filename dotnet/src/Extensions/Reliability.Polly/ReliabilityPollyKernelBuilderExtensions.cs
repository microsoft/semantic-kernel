// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Reliability.Polly;
using Polly;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of KernelConfig
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides extension methods for the <see cref="KernelBuilder"/>.
/// </summary>
public static class ReliabilityPollyKernelBuilderExtensions
{
    /// <summary>
    /// Sets the default retry configuration for any kernel http request.
    /// </summary>
    /// <param name="kernelConfig">Target instance</param>
    /// <param name="retryPolicy">Provided AsyncPolicy</param>
    /// <returns>Returns target instance for fluent compatibility</returns>
    public static KernelBuilder WithRetryPolly(this KernelBuilder kernelConfig, AsyncPolicy retryPolicy)
    {
        var pollyHandler = new PollyHttpRetryHandlerFactory(retryPolicy);
        return kernelConfig.WithHttpHandlerFactory(pollyHandler);
    }

    /// <summary>
    /// Sets the default retry configuration for any kernel http request.
    /// </summary>
    /// <param name="kernelConfig">Target instance</param>
    /// <param name="retryPolicy">Provided HttpResponseMessage AsyncPolicy</param>
    /// <returns>Returns target instance for fluent compatibility</returns>
    public static KernelBuilder WithRetryPolly(this KernelBuilder kernelConfig, AsyncPolicy<HttpResponseMessage> retryPolicy)
    {
        var pollyHandler = new PollyHttpRetryHandlerFactory(retryPolicy);
        return kernelConfig.WithHttpHandlerFactory(pollyHandler);
    }
}
