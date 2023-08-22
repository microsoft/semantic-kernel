// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Reliability;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the configuration for the Semantic Kernel.
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
    /// Sets the HTTP retry handler factory to use for the kernel.
    /// </summary>
    /// <param name="httpHandlerFactory">The HTTP retry handler factory to use. If null, the default factory will be used.</param>
    /// <returns>The updated kernel configuration.</returns>
    public KernelConfig SetHttpRetryHandlerFactory(IDelegatingHandlerFactory? httpHandlerFactory = null)
    {
        if (httpHandlerFactory != null)
        {
            this.HttpHandlerFactory = httpHandlerFactory;
        }

        return this;
    }

    /// <summary>
    /// Sets the default HTTP retry configuration for built-in HTTP handler factory.
    /// </summary>
    /// <param name="httpRetryConfig">The HTTP retry configuration to use. If null, the default configuration will be used.</param>
    /// <returns>The updated kernel configuration.</returns>
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
