// Copyright (c) Microsoft. All rights reserved.

using System;
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
    public IDelegatingHandlerFactory HttpHandlerFactory { get; private set; } = new NullHttpHandlerFactory();

    /// <summary>
    /// Default HTTP retry configuration for built-in HTTP handler factory.
    /// </summary>
    [Obsolete("Usage of Semantic Kernel internal retry abstractions is deprecated")]
    public HttpRetryConfig DefaultHttpRetryConfig =>
        throw new NotSupportedException("Usage of Semantic Kernel internal retry abstractions is deprecated");

    /// <summary>
    /// Set your custom http handler factory to use for the kernel.
    /// </summary>
    /// <param name="httpHandlerFactory">Http retry handler factory to use.</param>
    /// <returns>The updated kernel configuration.</returns>
    public KernelConfig SetHttpHandlerFactory(IDelegatingHandlerFactory? httpHandlerFactory = null)
    {
        this.HttpHandlerFactory = httpHandlerFactory ?? new NullHttpHandlerFactory();

        return this;
    }

    [Obsolete("Usage of Semantic Kernel internal retry abstractions is deprecated, provide a factory for custom http handling")]
    public KernelConfig SetDefaultHttpRetryConfig(HttpRetryConfig? httpRetryConfig)
    {
        throw new NotSupportedException("Usage of Semantic Kernel internal retry abstractions is deprecated");
    }
}
