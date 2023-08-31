// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Config;

namespace Microsoft.SemanticKernel.Reliability;

[Obsolete("Usage of Semantic Kernel internal retry abstractions is deprecated.\nCheck KernelSyntaxExamples.Example42_KernelBuilder.cs for alternatives")]
public class DefaultHttpRetryHandlerFactory : IDelegatingHandlerFactory
{
    public DefaultHttpRetryHandlerFactory(HttpRetryConfig? config = null)
    {
        this.Config = config;
    }

    public DelegatingHandler Create(ILoggerFactory? loggerFactory)
    {
        return new DefaultHttpRetryHandler(this.Config, loggerFactory);
    }

    public HttpRetryConfig? Config { get; }
}
