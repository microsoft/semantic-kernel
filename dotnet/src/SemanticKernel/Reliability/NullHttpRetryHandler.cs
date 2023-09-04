// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Reliability;

public class NullHttpRetryHandlerFactory : IDelegatingHandlerFactory
{
    public DelegatingHandler Create(ILoggerFactory? loggerFactory)
    {
        return new NullHttpRetryHandler();
    }
}

/// <summary>
/// A http retry handler that does not retry.
/// </summary>
public class NullHttpRetryHandler : DelegatingHandler
{
}
