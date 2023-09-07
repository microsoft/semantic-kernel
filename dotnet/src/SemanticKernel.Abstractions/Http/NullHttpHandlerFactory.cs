// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Http;

/// <summary>
/// Implementation of <see cref="IDelegatingHandlerFactory"/> that creates <see cref="NullHttpHandler"/> instances.
/// </summary>
public sealed class NullHttpHandlerFactory : IDelegatingHandlerFactory
{
    /// <summary>
    /// Gets the singleton instance of <see cref="NullHttpHandlerFactory"/>.
    /// </summary>
    public static NullHttpHandlerFactory Instance => new();

    /// <summary>
    /// Creates a new <see cref="NullHttpHandler"/> instance.
    /// </summary>
    /// <param name="loggerFactory">The logger factory to use.</param>
    /// <returns>A new <see cref="NullHttpHandler"/> instance.</returns>
    public DelegatingHandler Create(ILoggerFactory? loggerFactory)
    {
        return new NullHttpHandler();
    }
}
