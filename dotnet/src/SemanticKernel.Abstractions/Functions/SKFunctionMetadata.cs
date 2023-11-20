// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.Diagnostics;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides read-only metadata for an <see cref="ISKFunction"/>.
/// </summary>
public sealed class SKFunctionMetadata
{
    /// <summary>The name of the function.</summary>
    private string _name = string.Empty;
    /// <summary>The description of the function.</summary>
    private string _description = string.Empty;
    /// <summary>The function's parameters.</summary>
    private IReadOnlyList<SKParameterMetadata> _parameters = Array.Empty<SKParameterMetadata>();
    /// <summary>The function's return parameter.</summary>
    private SKReturnParameterMetadata? _returnParameter;

    /// <summary>Initializes the <see cref="SKFunctionMetadata"/> for a function with the specified name.</summary>
    /// <param name="name">The name of the function.</param>
    /// <exception cref="ArgumentNullException">The <paramref name="name"/> was null.</exception>
    /// <exception cref="ArgumentException">An invalid name was supplied.</exception>
    public SKFunctionMetadata(string name)
    {
        this.Name = name;
    }

    /// <summary>Initializes a <see cref="SKFunctionMetadata"/> as a copy of another <see cref="SKFunctionMetadata"/>.</summary>
    /// <exception cref="ArgumentNullException">The <paramref name="metadata"/> was null.</exception>
    /// <remarks>
    /// This creates a shallow clone of <paramref name="metadata"/>. The new instance's <see cref="Parameters"/> and
    /// <see cref="ReturnParameter"/> properties will return the same objects as in the original instance.
    /// </remarks>
    public SKFunctionMetadata(SKFunctionMetadata metadata)
    {
        Verify.NotNull(metadata);
        this.Name = metadata.Name;
        this.PluginName = metadata.PluginName;
        this.Description = metadata.Description;
        this.Parameters = metadata.Parameters;
        this.ReturnParameter = metadata.ReturnParameter;
    }

    /// <summary>Gets the name of the function.</summary>
    public string Name
    {
        get => this._name;
        init
        {
            Verify.NotNull(value);
            Verify.ValidFunctionName(value);
            this._name = value;
        }
    }

    /// <summary>Gets the name of the plugin containing the function.</summary>
    public string? PluginName { get; init; }

    /// <summary>Gets a description of the function, suitable for use in describing the purpose to a model.</summary>
    [AllowNull]
    public string Description
    {
        get => this._description;
        init => this._description = value ?? string.Empty;
    }

    /// <summary>Gets the metadata for the parameters to the function.</summary>
    /// <remarks>If the function has no parameters, the returned list will be empty.</remarks>
    public IReadOnlyList<SKParameterMetadata> Parameters
    {
        get => this._parameters;
        init
        {
            Verify.NotNull(value);
            this._parameters = value;
        }
    }

    /// <summary>Gets parameter metadata for the return parameter.</summary>
    /// <remarks>If the function has no return parameter, the returned value will be a default instance of a <see cref="SKReturnParameterMetadata"/>.</remarks>
    public SKReturnParameterMetadata ReturnParameter
    {
        get => this._returnParameter ??= new();
        init
        {
            Verify.NotNull(value);
            this._returnParameter = value;
        }
    }
}
