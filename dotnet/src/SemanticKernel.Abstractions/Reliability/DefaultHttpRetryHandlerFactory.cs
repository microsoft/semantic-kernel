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
        this.Config = config;
    }

    public DelegatingHandler Create(ILogger? logger)
    {
        return new DefaultHttpRetryHandler(this.Config, logger);
    }

    public HttpRetryConfig? Config { get; }
}
