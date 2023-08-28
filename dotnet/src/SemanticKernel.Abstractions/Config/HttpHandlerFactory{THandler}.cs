// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using System.Net.Http;
using System;

namespace Microsoft.SemanticKernel.Config;

public abstract class HttpHandlerFactory<THandler> : IDelegatingHandlerFactory where THandler : DelegatingHandler
{
    public DelegatingHandler Create(ILoggerFactory? loggerFactory)
    {
        return (DelegatingHandler)Activator.CreateInstance(typeof(THandler), loggerFactory);
    }
}
