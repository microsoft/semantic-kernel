// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using static Microsoft.SemanticKernel.KernelParameterMetadata;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides read-only metadata for a <see cref="KernelFunction"/>'s return parameter.
/// </summary>
public sealed class KernelReturnParameterMetadata
{
    internal static KernelReturnParameterMetadata Empty
    {
        [UnconditionalSuppressMessage("Trimming", "IL2026:Members annotated with 'RequiresUnreferencedCodeAttribute' require dynamic access otherwise can break functionality when trimming application code", Justification = "This method is AOT safe.")]
        [UnconditionalSuppressMessage("AOT", "IL3050:Calling members annotated with 'RequiresDynamicCodeAttribute' may break functionality when AOT compiling.", Justification = "This method is AOT safe.")]
        get
        {
            return s_empty ??= new KernelReturnParameterMetadata();
        }
    }

    /// <summary>The description of the return parameter.</summary>
    private string _description = string.Empty;
    /// <summary>The .NET type of the return parameter.</summary>
    private Type? _parameterType;
    /// <summary>The schema of the return parameter, potentially lazily-initialized.</summary>
    private KernelParameterMetadata.InitializedSchema? _schema;
    /// <summary>The serializer options to generate JSON schema.</summary>
    private readonly JsonSerializerOptions? _jsonSerializerOptions;
    /// <summary>The empty instance</summary>
    private static KernelReturnParameterMetadata? s_empty;

    /// <summary>Initializes the <see cref="KernelReturnParameterMetadata"/>.</summary>
    [RequiresUnreferencedCode("Uses reflection to generate schema, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to generate schema, making it incompatible with AOT scenarios.")]
    public KernelReturnParameterMetadata() { }

    /// <summary>Initializes the <see cref="KernelReturnParameterMetadata"/>.</summary>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to generate JSON schema.</param>
    public KernelReturnParameterMetadata(JsonSerializerOptions jsonSerializerOptions)
    {
        this._jsonSerializerOptions = jsonSerializerOptions;
    }

    /// <summary>Initializes a <see cref="KernelReturnParameterMetadata"/> as a copy of another <see cref="KernelReturnParameterMetadata"/>.</summary>
    [RequiresUnreferencedCode("Uses reflection, if no JSOs are available in the metadata, to generate the schema, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection, if no JSOs are available in the metadata, to generate the schema, making it incompatible with AOT scenarios.")]
    public KernelReturnParameterMetadata(KernelReturnParameterMetadata metadata)
    {
        this._description = metadata._description;
        this._parameterType = metadata._parameterType;
        this._schema = metadata._schema;
        this._jsonSerializerOptions = metadata._jsonSerializerOptions;
    }

    /// <summary>Initializes a <see cref="KernelReturnParameterMetadata"/> as a copy of another <see cref="KernelReturnParameterMetadata"/>.</summary>
    /// <param name="metadata">The metadata to copy.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to generate JSON schema.</param>
    public KernelReturnParameterMetadata(KernelReturnParameterMetadata metadata, JsonSerializerOptions jsonSerializerOptions)
    {
        this._description = metadata._description;
        this._parameterType = metadata._parameterType;
        this._schema = metadata._schema;
        this._jsonSerializerOptions = jsonSerializerOptions;
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
        [UnconditionalSuppressMessage("Trimming", "IL2026:Members annotated with 'RequiresUnreferencedCodeAttribute' require dynamic access otherwise can break functionality when trimming application code", Justification = "The warning is shown and should be addressed at the class creation site; no need to show it again at the members invocation sites.")]
        [UnconditionalSuppressMessage("AOT", "IL3050:Calling members annotated with 'RequiresDynamicCodeAttribute' may break functionality when AOT compiling.", Justification = "The warning is shown and should be addressed at the class creation site; no need to show it again at the members invocation sites.")]
        get => (this._schema ??= InferSchema(this.ParameterType, defaultValue: null, this.Description, this._jsonSerializerOptions)).Schema;
        init => this._schema = value is null ? null : new() { Inferred = false, Schema = value };
    }
}
