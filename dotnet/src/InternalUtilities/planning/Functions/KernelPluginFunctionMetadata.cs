// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

#pragma warning disable IDE0130

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides read-only metadata for an <see cref="KernelFunction"/>.
/// </summary>
public sealed class KernelPluginFunctionMetadata
{
    private readonly KernelFunctionMetadata _metadata;

    /// <summary>Initializes a <see cref="KernelPluginFunctionMetadata"/> as a copy of a <see cref="KernelFunctionMetadata"/>.</summary>
    /// <exception cref="ArgumentNullException">The <paramref name="metadata"/> was null.</exception>
    /// <remarks>
    /// This creates a shallow clone of <paramref name="metadata"/>. The new instance's <see cref="Parameters"/> and
    /// <see cref="ReturnParameter"/> properties will return the same objects as in the original instance.
    /// </remarks>
    public KernelPluginFunctionMetadata(KernelFunctionMetadata metadata)
    {
        Verify.NotNull(metadata);
        this._metadata = metadata;
    }

    /// <summary>Gets the name of the function.</summary>
    public string Name => this._metadata.Name;

    /// <summary>Gets the name of the plugin containing the function.</summary>
    public string? PluginName { get; init; }

    /// <summary>Gets a description of the function, suitable for use in describing the purpose to a model.</summary>
    [AllowNull]
    public string Description => this._metadata.Description;

    /// <summary>Gets the metadata for the parameters to the function.</summary>
    /// <remarks>If the function has no parameters, the returned list will be empty.</remarks>
    public IReadOnlyList<KernelParameterMetadata> Parameters => this._metadata.Parameters;

    /// <summary>Gets parameter metadata for the return parameter.</summary>
    /// <remarks>If the function has no return parameter, the returned value will be a default instance of a <see cref="KernelReturnParameterMetadata"/>.</remarks>
    public KernelReturnParameterMetadata ReturnParameter => this._metadata.ReturnParameter;

    /// <summary>Gets the <see cref="KernelFunctionMetadata"/> that this instance was created from.</summary>
    public KernelFunctionMetadata Metadata => this._metadata;
}
