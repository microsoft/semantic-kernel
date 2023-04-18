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

    public DelegatingHandler Create(ILogger? log)
    {
        return new DefaultHttpRetryHandler(this._config, log);
    }

    private readonly HttpRetryConfig? _config;
}
