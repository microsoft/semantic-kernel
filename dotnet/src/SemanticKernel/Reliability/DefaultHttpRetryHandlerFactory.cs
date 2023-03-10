// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Configuration;

namespace Microsoft.SemanticKernel.Reliability;

internal class DefaultHttpRetryHandlerFactory : IDelegatingHandlerFactory
{
    internal DefaultHttpRetryHandlerFactory(KernelConfig.HttpRetryConfig? config = null)
    {
        this._config = config;
    }

    public DelegatingHandler Create(ILogger log)
    {
        return new DefaultHttpRetryHandler(this._config, log);
    }

    private readonly KernelConfig.HttpRetryConfig? _config;
}
