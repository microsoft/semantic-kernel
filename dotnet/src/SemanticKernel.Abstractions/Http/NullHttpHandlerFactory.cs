// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Http;

internal sealed class NullHttpHandlerFactory : IDelegatingHandlerFactory
{
    public DelegatingHandler Create(ILoggerFactory? loggerFactory)
    {
        return new NullHttpHandler();
    }
}
