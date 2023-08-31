// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Config;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Reliability.Polly;

/// <summary>
/// Internal factory for creating <see cref="DefaultHttpRetryHandler"/> instances.
/// </summary>
internal sealed class DefaultHttpRetryHandlerFactory : HttpHandlerFactory<DefaultHttpRetryHandler>
{
    /// <summary>
    /// Creates a new instance of <see cref="DefaultHttpRetryHandlerFactory"/> with the provided configuration.
    /// </summary>
    /// <param name="config">Http retry configuration</param>
    internal DefaultHttpRetryHandlerFactory(HttpRetryConfig? config = null)
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
        return new DefaultHttpRetryHandler(this.Config, loggerFactory);
    }

    /// <summary>
    /// Creates a new instance of <see cref="DefaultHttpRetryHandler"/> with a specified configuration.
    /// </summary>
    /// <param name="config">Specific configuration</param>
    /// <param name="loggerFactory">Logger factory</param>
    /// <returns>Returns the created handler</returns>
    public DelegatingHandler Create(HttpRetryConfig config, ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(config, nameof(config));

        return new DefaultHttpRetryHandler(config, loggerFactory);
    }

    /// <summary>
    /// Default retry configuration used when creating a new instance of <see cref="DefaultHttpRetryHandler"/>.
    /// </summary>
    internal HttpRetryConfig Config { get; }
}
