// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Reliability;

[Obsolete("Usage of Semantic Kernel internal retry abstractions is deprecated")]
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
