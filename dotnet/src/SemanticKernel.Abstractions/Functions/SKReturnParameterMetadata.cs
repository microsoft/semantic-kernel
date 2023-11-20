// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides read-only metadata for an <see cref="ISKFunction"/>'s return parameter.
/// </summary>
public sealed class SKReturnParameterMetadata
{
    /// <summary>The description of the return parameter.</summary>
    private string _description = string.Empty;

    /// <summary>Initializes the <see cref="SKReturnParameterMetadata"/>.</summary>
    public SKReturnParameterMetadata()
    {
    }

    /// <summary>Initializes a <see cref="SKReturnParameterMetadata"/> as a copy of another <see cref="SKReturnParameterMetadata"/>.</summary>
    public SKReturnParameterMetadata(SKReturnParameterMetadata metadata)
    {
        this.Description = metadata.Description;
        this.ParameterType = metadata.ParameterType;
        this.Schema = metadata.Schema;
    }

    /// <summary>Gets a description of the return parameter, suitable for use in describing the purpose to a model.</summary>
    [AllowNull]
    public string Description
    {
        get => this._description;
        init => this._description = value ?? string.Empty;
    }

    /// <summary>Gets the .NET type of the return parameter.</summary>
    public Type? ParameterType { get; init; }

    /// <summary>Gets a JSON Schema describing the type of the return parameter.</summary>
    public SKJsonSchema? Schema { get; init; }
}
