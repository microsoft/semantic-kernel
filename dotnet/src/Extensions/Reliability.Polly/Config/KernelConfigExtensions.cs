// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Reliability.Polly.Config;

public static class KernelConfigExtensions
{
    /// <summary>
    /// Sets the default retry configuration for any kernel http request.
    /// </summary>
    /// <param name="kernelConfig">Target instance</param>
    /// <param name="retryConfig">Retry configuration</param>
    /// <returns>Returns target instance for fluent compatibility</returns>
    public static KernelConfig SetHttpRetryConfig(this KernelConfig kernelConfig, HttpRetryConfig? retryConfig = null)
    {
        var pollyHandler = new DefaultHttpRetryHandlerFactory(retryConfig);
        kernelConfig.SetHttpHandlerFactory(pollyHandler);
        return kernelConfig;
    }
}
