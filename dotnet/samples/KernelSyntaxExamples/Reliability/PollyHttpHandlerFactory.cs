// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Reliability;

namespace Reliability;

public class PollyHttpHandlerFactory<THandler> : IDelegatingHandlerFactory where THandler : DelegatingHandler
{
    public DelegatingHandler Create(ILogger? logger)
    {
        return (DelegatingHandler)Activator.CreateInstance(typeof(THandler), logger)!;
    }
}
