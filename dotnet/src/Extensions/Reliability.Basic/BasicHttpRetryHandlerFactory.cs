// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Reliability.Basic;

/// <summary>
/// Internal factory for creating <see cref="DefaultHttpRetryHandler"/> instances.
/// </summary>
public sealed class BasicHttpRetryHandlerFactory : HttpHandlerFactory<BasicHttpRetryHandler>
{
    /// <summary>
    /// Gets the singleton instance of <see cref="DefaultHttpRetryHandlerFactory"/>.
    /// </summary>
    public static BasicHttpRetryHandlerFactory Instance { get; } = new BasicHttpRetryHandlerFactory();

    /// <summary>
    /// Creates a new instance of <see cref="DefaultHttpRetryHandlerFactory"/> with the provided configuration.
    /// </summary>
    /// <param name="config">Http retry configuration</param>
    internal BasicHttpRetryHandlerFactory(BasicRetryConfig? config = null)
    {
        this.Config = config ?? new();
    }

    /// <summary>
    /// Creates a new instance of <see cref="DefaultHttpRetryHandler"/> with the default configuration.
    /// </summary>
    /// <param name="loggerFactory">Logger factory</param>
    /// <returns>Returns the created handler</returns>
    public override DelegatingHandler Create(ILoggerFactory? loggerFactory = null)
    {
        return new BasicHttpRetryHandler(this.Config, loggerFactory);
    }

    /// <summary>
    /// Creates a new instance of <see cref="DefaultHttpRetryHandler"/> with a specified configuration.
    /// </summary>
    /// <param name="config">Specific configuration</param>
    /// <param name="loggerFactory">Logger factory</param>
    /// <returns>Returns the created handler</returns>
    public DelegatingHandler Create(BasicRetryConfig config, ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(config, nameof(config));

        return new BasicHttpRetryHandler(config, loggerFactory);
    }

    /// <summary>
    /// Default retry configuration used when creating a new instance of <see cref="DefaultHttpRetryHandler"/>.
    /// </summary>
    internal BasicRetryConfig Config { get; }
}
