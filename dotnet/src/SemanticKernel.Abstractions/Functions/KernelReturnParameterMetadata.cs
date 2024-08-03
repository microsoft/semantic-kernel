// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using static Microsoft.SemanticKernel.KernelParameterMetadata;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides read-only metadata for a <see cref="KernelFunction"/>'s return parameter.
/// </summary>
public sealed class KernelReturnParameterMetadata
{
    internal static readonly KernelReturnParameterMetadata Empty = new();

    /// <summary>The description of the return parameter.</summary>
    private string _description = string.Empty;
    /// <summary>The .NET type of the return parameter.</summary>
    private Type? _parameterType;
    /// <summary>The schema of the return parameter, potentially lazily-initialized.</summary>
    private KernelParameterMetadata.InitializedSchema? _schema;

    /// <summary>Initializes the <see cref="KernelReturnParameterMetadata"/>.</summary>
    public KernelReturnParameterMetadata() { }

    /// <summary>Initializes a <see cref="KernelReturnParameterMetadata"/> as a copy of another <see cref="KernelReturnParameterMetadata"/>.</summary>
    public KernelReturnParameterMetadata(KernelReturnParameterMetadata metadata)
    {
        this._description = metadata._description;
        this._parameterType = metadata._parameterType;
        this._schema = metadata._schema;
    }

    /// <summary>Gets a description of the return parameter, suitable for use in describing the purpose to a model.</summary>
    [AllowNull]
    public string Description
    {
        get => this._description;
        init
        {
            string newDescription = value ?? string.Empty;
            if (value != this._description && this._schema?.Inferred is true)
            {
                this._schema = null;
            }
            this._description = newDescription;
        }
    }

    /// <summary>Gets the .NET type of the return parameter.</summary>
    public Type? ParameterType
    {
        get => this._parameterType;
        init
        {
            if (value != this._parameterType && this._schema?.Inferred is true)
            {
                this._schema = null;
            }
            this._parameterType = value;
        }
    }

    /// <summary>Gets a JSON Schema describing the type of the return parameter.</summary>
    public KernelJsonSchema? Schema
    {
        get => (this._schema ??= InferSchema(this.ParameterType, defaultValue: null, this.Description)).Schema;
        init => this._schema = value is null ? null : new() { Inferred = false, Schema = value };
    }
}
