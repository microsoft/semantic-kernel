// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Config;

public abstract class HttpHandlerFactory<THandler> : IDelegatingHandlerFactory where THandler : DelegatingHandler
{
    public virtual DelegatingHandler Create(ILoggerFactory? loggerFactory)
    {
        return (DelegatingHandler)Activator.CreateInstance(typeof(THandler), loggerFactory);
    }
}
