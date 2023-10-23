// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Http;

/// <summary>
/// A factory for creating instances of <see cref="DelegatingHandler"/>.
/// </summary>
/// <typeparam name="THandler"></typeparam>
public abstract class HttpHandlerFactory<THandler> : IDelegatingHandlerFactory where THandler : DelegatingHandler
{
    /// <summary>
    /// Creates a new instance of <see cref="DelegatingHandler"/>.
    /// </summary>
    /// <param name="loggerFactory"></param>
    /// <returns></returns>
    public virtual DelegatingHandler Create(ILoggerFactory? loggerFactory = null)
    {
        return (DelegatingHandler)Activator.CreateInstance(typeof(THandler), loggerFactory);
    }
}
