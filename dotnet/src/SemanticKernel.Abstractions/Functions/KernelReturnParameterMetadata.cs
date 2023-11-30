// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides read-only metadata for a <see cref="KernelFunction"/>'s return parameter.
/// </summary>
public sealed class KernelReturnParameterMetadata
{
    /// <summary>The description of the return parameter.</summary>
    private string _description = string.Empty;

    /// <summary>Initializes the <see cref="KernelReturnParameterMetadata"/>.</summary>
    public KernelReturnParameterMetadata()
    {
    }

    /// <summary>Initializes a <see cref="KernelReturnParameterMetadata"/> as a copy of another <see cref="KernelReturnParameterMetadata"/>.</summary>
    public KernelReturnParameterMetadata(KernelReturnParameterMetadata metadata)
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
    public KernelJsonSchema? Schema { get; init; }
}
