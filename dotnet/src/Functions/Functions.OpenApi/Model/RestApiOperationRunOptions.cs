// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Options for REST API operation run.
/// </summary>
internal sealed class RestApiOperationRunOptions
{
    /// <summary>
    /// Override for REST API operation server URL.
    /// </summary>
    public Uri? ServerUrlOverride { get; set; }

    /// <summary>
    /// The URL of REST API host.
    /// </summary>
    public Uri? ApiHostUrl { get; set; }

    /// <summary>
    /// The Kernel instance used for the operation run.
    /// </summary>
    public Kernel? Kernel { get; set; }

    /// <summary>
    /// The Kernel function whose invocation triggered the operation run.
    /// </summary>
    public KernelFunction? KernelFunction { get; set; }

    /// <summary>
    /// The Kernel arguments whose associated with the operation run.
    /// </summary>
    public KernelArguments? KernelArguments { get; set; }
}
