// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Reliability;

#pragma warning disable IDE0130 // Namespace does not match folder structure

namespace Microsoft.SemanticKernel;

/// <summary>
/// Semantic kernel configuration.
/// </summary>
public sealed class KernelConfig
{
    /// <summary>
    /// Kernel HTTP handler factory.
    /// </summary>
    public IDelegatingHandlerFactory HttpHandlerFactory { get; set; } = new NullHttpHandlerFactory();

    /// <summary>
    /// Deprecated. Sets the default HTTP retry configuration for built-in HTTP handler factory.
    /// </summary>
    /// <param name="httpRetryConfig">The HTTP retry configuration to use. If null, the default configuration will be used.</param>
    /// <returns>The updated kernel configuration.</returns>
    [Obsolete("Usage of Semantic Kernel internal core retry abstractions is deprecated, use a Resiliency extension package")]
    public KernelConfig SetDefaultHttpRetryConfig(HttpRetryConfig? httpRetryConfig)
    {
        throw new NotSupportedException("Usage of Semantic Kernel internal core retry abstractions is deprecated, use a Reliability extension package for a similar result");
    }
}
