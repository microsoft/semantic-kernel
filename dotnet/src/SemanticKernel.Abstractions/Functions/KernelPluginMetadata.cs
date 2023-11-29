// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides read-only metadata for an <see cref="IKernelPlugin"/>.
/// </summary>
public sealed class KernelPluginMetadata
{
    /// <summary>The name of the plugin.</summary>
    private string _name = string.Empty;
    /// <summary>The description of the plugin.</summary>
    private string _description = string.Empty;
    /// <summary>The plugin function's metadata.</summary>
    private IReadOnlyList<KernelFunctionMetadata> _functionsMetadata = Array.Empty<KernelFunctionMetadata>();

    /// <summary>Initializes the <see cref="KernelFunctionMetadata"/> for a function with the specified name.</summary>
    /// <param name="name">The name of the function.</param>
    /// <exception cref="ArgumentNullException">The <paramref name="name"/> was null.</exception>
    /// <exception cref="ArgumentException">An invalid name was supplied.</exception>
    public KernelPluginMetadata(string name)
    {
        this.Name = name;
    }

    /// <summary>Gets the name of the plugin.</summary>
    public string Name
    {
        get => this._name;
        init
        {
            Verify.NotNull(value);
            Verify.ValidPluginName(value);
            this._name = value;
        }
    }

    /// <summary>Gets a description of the plugin, suitable for use in describing the purpose to a model.</summary>
    [AllowNull]
    public string Description
    {
        get => this._description;
        init => this._description = value ?? string.Empty;
    }

    /// <summary>Gets the metadata for the functions to the plugin.</summary>
    /// <remarks>If the plugin has no functions, the returned list will be empty.</remarks>
    public IReadOnlyList<KernelFunctionMetadata> FunctionsMetadata
    {
        get => this._functionsMetadata;
        init
        {
            Verify.NotNull(value);
            this._functionsMetadata = value;
        }
    }
}
