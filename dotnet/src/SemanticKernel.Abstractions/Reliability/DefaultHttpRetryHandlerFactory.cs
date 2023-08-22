// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Reliability;
/// <summary>
/// A factory class for creating instances of <see cref="DefaultHttpRetryHandler"/>.
/// Implements the <see cref="IDelegatingHandlerFactory"/> interface.
/// </summary>
/// <example>
/// To create a new instance of <see cref="DefaultHttpRetryHandler"/> with a custom configuration:
/// <code>
/// var config = new HttpRetryConfig { MaxRetries = 5 };
/// var factory = new DefaultHttpRetryHandlerFactory(config);
/// var handler = factory.Create(logger);
/// </code>
/// </example>
public class DefaultHttpRetryHandlerFactory : IDelegatingHandlerFactory
{
    /// <summary>
    /// Initializes a new instance of the <see cref="DefaultHttpRetryHandlerFactory"/> class.
    /// </summary>
    /// <param name="config">An optional <see cref="HttpRetryConfig"/> instance to configure the retry behavior. If not provided, default configuration will be used.</param>
    public DefaultHttpRetryHandlerFactory(HttpRetryConfig? config = null)
    {
        this.Config = config;
    }

    /// <summary>
    /// Creates a new instance of <see cref="DefaultHttpRetryHandler"/> with the specified logger.
    /// </summary>
    /// <param name="logger">An optional <see cref="ILogger"/> instance to log retry events. If not provided, no logging will occur.</param>
    /// <returns>A new instance of <see cref="DefaultHttpRetryHandler"/>.</returns>
    public DelegatingHandler Create(ILogger? logger)
    {
        return new DefaultHttpRetryHandler(this.Config, logger);
    }

    /// <summary>
    /// Gets the <see cref="HttpRetryConfig"/> instance used to configure the retry behavior.
    /// </summary>
    public HttpRetryConfig? Config { get; }
}
