// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Config;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Reliability;

#pragma warning disable IDE0130 // Namespace does not match folder structure

namespace Microsoft.SemanticKernel;

/// <summary>
/// Semantic kernel configuration.
/// </summary>
public sealed class KernelConfig
{
    /// <summary>
    /// Factory for creating HTTP handlers.
    /// </summary>
    public IDelegatingHandlerFactory HttpHandlerFactory { get; private set; } = new NullHttpHandlerFactory();

    /// <summary>
    /// Set the http handler factory to use for the kernel.
    /// </summary>
    /// <param name="httpHandlerFactory">Http handler factory to use.</param>
    /// <returns>The updated kernel configuration.</returns>
    public KernelConfig SetHttpHandlerFactory(IDelegatingHandlerFactory httpHandlerFactory)
    {
        Verify.NotNull(httpHandlerFactory, nameof(httpHandlerFactory));

        this.HttpHandlerFactory = httpHandlerFactory;

        return this;
    }

    [Obsolete("Usage of Semantic Kernel internal core retry abstractions is deprecated, use a Resiliency extension package")]
    public KernelConfig SetDefaultHttpRetryConfig(HttpRetryConfig? httpRetryConfig)
    {
        throw new NotSupportedException("Usage of Semantic Kernel internal core retry abstractions is deprecated, use a Reliability extension package for a similar result");
    }
}
