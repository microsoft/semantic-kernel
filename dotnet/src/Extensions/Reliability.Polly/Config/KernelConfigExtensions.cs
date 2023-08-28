// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Reliability.Polly.Config;

public static class KernelConfigExtensions
{
    public static KernelConfig SetHttpRetryConfig(this KernelConfig kernelConfig, HttpRetryConfig config)
    {
        var pollyHandler = new DefaultHttpRetryHandlerFactory();
        kernelConfig.SetHttpHandlerFactory(pollyHandler);
        return kernelConfig;
    }
}
