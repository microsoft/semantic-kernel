// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Http;

/// <summary>
/// Implementation of <see cref="IDelegatingHandlerFactory"/> that creates <see cref="NullHttpHandler"/> instances.
/// </summary>
public sealed class NullHttpHandlerFactory : IDelegatingHandlerFactory
{
    public static NullHttpHandlerFactory Instance => new();

    public DelegatingHandler Create(ILoggerFactory? loggerFactory)
    {
        return new NullHttpHandler();
    }
}
