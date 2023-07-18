// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Reliability;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Semantic kernel configuration.
/// TODO: use .NET ServiceCollection (will require a lot of changes)
/// </summary>
public sealed class KernelConfig
{
    /// <summary>
    /// Factory for creating HTTP handlers.
    /// </summary>
    public IDelegatingHandlerFactory HttpHandlerFactory { get; private set; } = new DefaultHttpRetryHandlerFactory(new HttpRetryConfig());

    /// <summary>
    /// Default HTTP retry configuration for built-in HTTP handler factory.
    /// </summary>
    public HttpRetryConfig DefaultHttpRetryConfig { get; private set; } = new();

    /// <summary>
    /// Set the http retry handler factory to use for the kernel.
    /// </summary>
    /// <param name="httpHandlerFactory">Http retry handler factory to use.</param>
    /// <returns>The updated kernel configuration.</returns>
    public KernelConfig SetHttpRetryHandlerFactory(IDelegatingHandlerFactory? httpHandlerFactory = null)
    {
        if (httpHandlerFactory != null)
        {
            this.HttpHandlerFactory = httpHandlerFactory;
        }

        return this;
    }

    public KernelConfig SetDefaultHttpRetryConfig(HttpRetryConfig? httpRetryConfig)
    {
        if (httpRetryConfig != null)
        {
            this.DefaultHttpRetryConfig = httpRetryConfig;
            this.SetHttpRetryHandlerFactory(new DefaultHttpRetryHandlerFactory(httpRetryConfig));
        }

        return this;
    }
}
