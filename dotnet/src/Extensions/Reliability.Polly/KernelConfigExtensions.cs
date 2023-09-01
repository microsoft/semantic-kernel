// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130 // Namespace does not match folder structure

using System.Net.Http;
using Microsoft.SemanticKernel.Reliability.Polly;
using Polly;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for <see cref="KernelConfig"/> class.
/// </summary>
public static class KernelConfigExtensions
{
    /// <summary>
    /// Sets the default retry configuration for any kernel http request.
    /// </summary>
    /// <param name="kernelConfig">Target instance</param>
    /// <param name="retryPolicy">Provided AsyncPolicy</param>
    /// <returns>Returns target instance for fluent compatibility</returns>
    public static KernelConfig SetRetryPolly(this KernelConfig kernelConfig, AsyncPolicy retryPolicy)
    {
        var pollyHandler = new PollyHttpRetryHandlerFactory(retryPolicy);
        kernelConfig.SetHttpHandlerFactory(pollyHandler);
        return kernelConfig;
    }

    /// <summary>
    /// Sets the default retry configuration for any kernel http request.
    /// </summary>
    /// <param name="kernelConfig">Target instance</param>
    /// <param name="retryPolicy">Provided HttpResponseMessage AsyncPolicy</param>
    /// <returns>Returns target instance for fluent compatibility</returns>
    public static KernelConfig SetRetryPolly(this KernelConfig kernelConfig, AsyncPolicy<HttpResponseMessage> retryPolicy)
    {
        var pollyHandler = new PollyHttpRetryHandlerFactory(retryPolicy);
        kernelConfig.SetHttpHandlerFactory(pollyHandler);
        return kernelConfig;
    }
}
