// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Class with data related to an Open API <see cref="KernelFunction"/> invocation.
/// </summary>
public sealed class OpenApiKernelFunctionContext
{
    /// <summary>
    /// Key to access the <see cref="OpenApiKernelFunctionContext"/> in the <see cref="HttpRequestMessage"/>.
    /// </summary>
#if NET
    public static readonly HttpRequestOptionsKey<OpenApiKernelFunctionContext> KernelFunctionContextKey = new("KernelFunctionContext");
#else
    public static readonly string KernelFunctionContextKey = "KernelFunctionContext";
#endif

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenApiKernelFunctionContext"/> class.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> associated with this context.</param>
    /// <param name="function">The <see cref="KernelFunction"/> associated with this context.</param>
    /// <param name="arguments">The <see cref="KernelArguments"/> associated with this context.</param>
    internal OpenApiKernelFunctionContext(Kernel? kernel, KernelFunction? function, KernelArguments? arguments)
    {
        this.Kernel = kernel;
        this.Function = function;
        this.Arguments = arguments;
    }

    /// <summary>
    /// Gets the <see cref="Kernel"/>.
    /// </summary>
    public Kernel? Kernel { get; }

    /// <summary>
    /// Gets the <see cref="KernelFunction"/>.
    /// </summary>
    public KernelFunction? Function { get; }

    /// <summary>
    /// Gets the <see cref="KernelArguments"/>.
    /// </summary>
    public KernelArguments? Arguments { get; }
}
