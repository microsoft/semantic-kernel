// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Reliability;

public class DefaultHttpRetryHandlerFactory : IDelegatingHandlerFactory
{
    public DefaultHttpRetryHandlerFactory(HttpRetryConfig? config = null)
    {
        this._config = config;
    }

    public DelegatingHandler Create(ILogger? logger)
    {
        return new DefaultHttpRetryHandler(this._config, logger);
    }

    private readonly HttpRetryConfig? _config;
}
