// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
using System.Text.Json;
>>>>>>> origin/main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
using static Microsoft.SemanticKernel.KernelParameterMetadata;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides read-only metadata for a <see cref="KernelFunction"/>'s return parameter.
/// </summary>
public sealed class KernelReturnParameterMetadata
{
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    internal static readonly KernelReturnParameterMetadata Empty = new();
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
    internal static readonly KernelReturnParameterMetadata Empty = new();
=======
    internal static KernelReturnParameterMetadata Empty
    {
        [UnconditionalSuppressMessage("Trimming", "IL2026:Members annotated with 'RequiresUnreferencedCodeAttribute' require dynamic access otherwise can break functionality when trimming application code", Justification = "This method is AOT safe.")]
        [UnconditionalSuppressMessage("AOT", "IL3050:Calling members annotated with 'RequiresDynamicCodeAttribute' may break functionality when AOT compiling.", Justification = "This method is AOT safe.")]
        get
        {
            return s_empty ??= new KernelReturnParameterMetadata();
        }
    }
>>>>>>> origin/main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    /// <summary>The description of the return parameter.</summary>
    private string _description = string.Empty;
    /// <summary>The .NET type of the return parameter.</summary>
    private Type? _parameterType;
    /// <summary>The schema of the return parameter, potentially lazily-initialized.</summary>
    private KernelParameterMetadata.InitializedSchema? _schema;
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    /// <summary>Initializes the <see cref="KernelReturnParameterMetadata"/>.</summary>
    public KernelReturnParameterMetadata() { }

    /// <summary>Initializes a <see cref="KernelReturnParameterMetadata"/> as a copy of another <see cref="KernelReturnParameterMetadata"/>.</summary>
=======
=======
>>>>>>> Stashed changes
<<<<<<< main

    /// <summary>Initializes the <see cref="KernelReturnParameterMetadata"/>.</summary>
    public KernelReturnParameterMetadata() { }
=======
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
>>>>>>> origin/main

    /// <summary>Initializes a <see cref="KernelReturnParameterMetadata"/> as a copy of another <see cref="KernelReturnParameterMetadata"/>.</summary>
    [RequiresUnreferencedCode("Uses reflection, if no JSOs are available in the metadata, to generate the schema, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection, if no JSOs are available in the metadata, to generate the schema, making it incompatible with AOT scenarios.")]
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    public KernelReturnParameterMetadata(KernelReturnParameterMetadata metadata)
    {
        this._description = metadata._description;
        this._parameterType = metadata._parameterType;
        this._schema = metadata._schema;
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
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
>>>>>>> origin/main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        get => (this._schema ??= InferSchema(this.ParameterType, defaultValue: null, this.Description)).Schema;
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
        get => (this._schema ??= InferSchema(this.ParameterType, defaultValue: null, this.Description)).Schema;
=======
        [RequiresUnreferencedCode("Uses reflection to generate schema if no JSOs are provided at construction time, making it incompatible with AOT scenarios.")]
        [RequiresDynamicCode("Uses reflection to generate schema if no JSOs are provided at construction time, making it incompatible with AOT scenarios.")]
        get => (this._schema ??= InferSchema(this.ParameterType, defaultValue: null, this.Description, this._jsonSerializerOptions)).Schema;
>>>>>>> origin/main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        init => this._schema = value is null ? null : new() { Inferred = false, Schema = value };
    }
}
