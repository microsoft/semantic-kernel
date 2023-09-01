// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130 // Namespace does not match folder structure

using Microsoft.SemanticKernel.Reliability.Basic;

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
    /// <param name="retryConfig">Retry configuration</param>
    /// <returns>Returns target instance for fluent compatibility</returns>
    public static KernelConfig SetRetryBasic(this KernelConfig kernelConfig, BasicRetryConfig? retryConfig = null)
    {
        var httpHandler = new BasicHttpRetryHandlerFactory(retryConfig);
        kernelConfig.SetHttpHandlerFactory(httpHandler);
        return kernelConfig;
    }
}
