<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides read-only metadata for a <see cref="KernelFunction"/> parameter.
/// </summary>
public sealed class KernelParameterMetadata
{
    /// <summary>The name of the parameter.</summary>
    private string _name = string.Empty;
    /// <summary>The description of the parameter.</summary>
    private string _description = string.Empty;
    /// <summary>The default value of the parameter.</summary>
    private object? _defaultValue;
    /// <summary>The .NET type of the parameter.</summary>
    private Type? _parameterType;
    /// <summary>The schema of the parameter, potentially lazily-initialized.</summary>
    private InitializedSchema? _schema;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
    /// <summary>The serializer options to generate JSON schema.</summary>
    private readonly JsonSerializerOptions? _jsonSerializerOptions;
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    /// <summary>Initializes the <see cref="KernelParameterMetadata"/> for a parameter with the specified name.</summary>
    /// <param name="name">The name of the parameter.</param>
    /// <exception cref="ArgumentNullException">The <paramref name="name"/> was null.</exception>
    /// <exception cref="ArgumentException">The <paramref name="name"/> was empty or composed entirely of whitespace.</exception>
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    public KernelParameterMetadata(string name) => this.Name = name;

    /// <summary>Initializes a <see cref="KernelParameterMetadata"/> as a copy of another <see cref="KernelParameterMetadata"/>.</summary>
    /// <exception cref="ArgumentNullException">The <paramref name="metadata"/> was null.</exception>
    /// <remarks>This creates a shallow clone of <paramref name="metadata"/>.</remarks>
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    public KernelParameterMetadata(string name) => this.Name = name;
=======
    [RequiresUnreferencedCode("Uses reflection to generate schema, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to generate schema, making it incompatible with AOT scenarios.")]
    public KernelParameterMetadata(string name) => this.Name = name;
<<<<<<< Updated upstream
=======
    /// <summary>The serializer options to generate JSON schema.</summary>
    private readonly JsonSerializerOptions? _jsonSerializerOptions;
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

    /// <summary>Initializes the <see cref="KernelParameterMetadata"/> for a parameter with the specified name.</summary>
    /// <param name="name">The name of the parameter.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to generate JSON schema.</param>
    /// <exception cref="ArgumentNullException">The <paramref name="name"/> was null.</exception>
    /// <exception cref="ArgumentException">The <paramref name="name"/> was empty or composed entirely of whitespace.</exception>
<<<<<<< Updated upstream
<<<<<<< head
=======
    [RequiresUnreferencedCode("Uses reflection to generate schema, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to generate schema, making it incompatible with AOT scenarios.")]
    public KernelParameterMetadata(string name) => this.Name = name;

    /// <summary>Initializes the <see cref="KernelParameterMetadata"/> for a parameter with the specified name.</summary>
    /// <param name="name">The name of the parameter.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to generate JSON schema.</param>
    /// <exception cref="ArgumentNullException">The <paramref name="name"/> was null.</exception>
    /// <exception cref="ArgumentException">The <paramref name="name"/> was empty or composed entirely of whitespace.</exception>
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    public KernelParameterMetadata(string name, JsonSerializerOptions jsonSerializerOptions)
    {
        this.Name = name;
        this._jsonSerializerOptions = jsonSerializerOptions;
    }
>>>>>>> origin/main

    /// <summary>Initializes a <see cref="KernelParameterMetadata"/> as a copy of another <see cref="KernelParameterMetadata"/>.</summary>
    /// <exception cref="ArgumentNullException">The <paramref name="metadata"/> was null.</exception>
    /// <remarks>This creates a shallow clone of <paramref name="metadata"/>.</remarks>
    [RequiresUnreferencedCode("Uses reflection, if no JSOs are available in the metadata, to generate the schema, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection, if no JSOs are available in the metadata, to generate the schema, making it incompatible with AOT scenarios.")]
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    public KernelParameterMetadata(KernelParameterMetadata metadata)
    {
        Verify.NotNull(metadata);
        this._name = metadata._name;
        this._description = metadata._description;
        this._defaultValue = metadata._defaultValue;
<<<<<<< Updated upstream
<<<<<<< head
        this.IsRequired = metadata.IsRequired;
        this._parameterType = metadata._parameterType;
        this._schema = metadata._schema;
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        this.IsRequired = metadata.IsRequired;
        this._parameterType = metadata._parameterType;
        this._schema = metadata._schema;
>>>>>>> Stashed changes
<<<<<<< main
=======
        this._jsonSerializerOptions = metadata._jsonSerializerOptions;
    }

    /// <summary>Initializes a <see cref="KernelParameterMetadata"/> as a copy of another <see cref="KernelParameterMetadata"/>.</summary>
    /// <exception cref="ArgumentNullException">The <paramref name="metadata"/> was null.</exception>
    /// <param name="metadata">The metadata to copy.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to generate JSON schema.</param>
    /// <remarks>This creates a shallow clone of <paramref name="metadata"/>.</remarks>
    public KernelParameterMetadata(KernelParameterMetadata metadata, JsonSerializerOptions jsonSerializerOptions)
    {
        Verify.NotNull(metadata);
        this._name = metadata._name;
        this._description = metadata._description;
        this._defaultValue = metadata._defaultValue;
        this.IsRequired = metadata.IsRequired;
        this._parameterType = metadata._parameterType;
        this._schema = metadata._schema;
        this._jsonSerializerOptions = jsonSerializerOptions;
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        this.IsRequired = metadata.IsRequired;
        this._parameterType = metadata._parameterType;
        this._schema = metadata._schema;
        this._jsonSerializerOptions = metadata._jsonSerializerOptions;
    }

    /// <summary>Initializes a <see cref="KernelParameterMetadata"/> as a copy of another <see cref="KernelParameterMetadata"/>.</summary>
    /// <exception cref="ArgumentNullException">The <paramref name="metadata"/> was null.</exception>
    /// <param name="metadata">The metadata to copy.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to generate JSON schema.</param>
    /// <remarks>This creates a shallow clone of <paramref name="metadata"/>.</remarks>
    public KernelParameterMetadata(KernelParameterMetadata metadata, JsonSerializerOptions jsonSerializerOptions)
    {
        Verify.NotNull(metadata);
        this._name = metadata._name;
        this._description = metadata._description;
        this._defaultValue = metadata._defaultValue;
        this.IsRequired = metadata.IsRequired;
        this._parameterType = metadata._parameterType;
        this._schema = metadata._schema;
        this._jsonSerializerOptions = jsonSerializerOptions;
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    }

    /// <summary>Gets the name of the function.</summary>
    public string Name
    {
        get => this._name;
        init
        {
            Verify.NotNullOrWhiteSpace(value);
            this._name = value;
        }
    }

    /// <summary>Gets a description of the function, suitable for use in describing the purpose to a model.</summary>
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

    /// <summary>Gets the default value of the parameter.</summary>
    public object? DefaultValue
    {
        get => this._defaultValue;
        init
        {
            if (value != this._defaultValue && this._schema?.Inferred is true)
            {
                this._schema = null;
            }
            this._defaultValue = value;
        }
    }

    /// <summary>Gets whether the parameter is required.</summary>
    public bool IsRequired { get; init; }

    /// <summary>Gets the .NET type of the parameter.</summary>
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

    /// <summary>Gets a JSON Schema describing the parameter's type.</summary>
    public KernelJsonSchema? Schema
    {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        get => (this._schema ??= InferSchema(this.ParameterType, this.DefaultValue, this.Description)).Schema;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        get => (this._schema ??= InferSchema(this.ParameterType, this.DefaultValue, this.Description)).Schema;
=======
        [RequiresUnreferencedCode("Uses reflection if created with a non-AOT compatible constructor, making it incompatible with AOT scenarios.")]
        [RequiresDynamicCode("Uses reflection if created with a non-AOT compatible constructor, making it incompatible with AOT scenarios.")]
        get => (this._schema ??= InferSchema(this.ParameterType, this.DefaultValue, this.Description, this._jsonSerializerOptions)).Schema;
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        [RequiresUnreferencedCode("Uses reflection if created with a non-AOT compatible constructor, making it incompatible with AOT scenarios.")]
        [RequiresDynamicCode("Uses reflection if created with a non-AOT compatible constructor, making it incompatible with AOT scenarios.")]
        get => (this._schema ??= InferSchema(this.ParameterType, this.DefaultValue, this.Description, this._jsonSerializerOptions)).Schema;
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        init => this._schema = value is null ? null : new() { Inferred = false, Schema = value };
    }

    /// <summary>Infers a JSON schema from a <see cref="Type"/> and description.</summary>
    /// <param name="parameterType">The parameter type. If null, no schema can be inferred.</param>
    /// <param name="defaultValue">The parameter's default value, if any.</param>
    /// <param name="description">The parameter description. If null, it won't be included in the schema.</param>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    internal static InitializedSchema InferSchema(Type? parameterType, object? defaultValue, string? description)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    internal static InitializedSchema InferSchema(Type? parameterType, object? defaultValue, string? description)
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
    internal static InitializedSchema InferSchema(Type? parameterType, object? defaultValue, string? description)
=======
>>>>>>> Stashed changes
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to generate JSON schema.</param>
    [RequiresUnreferencedCode("Uses reflection if no JSOs are provided, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection if no JSOs are provided, making it incompatible with AOT scenarios.")]
    internal static InitializedSchema InferSchema(Type? parameterType, object? defaultValue, string? description, JsonSerializerOptions? jsonSerializerOptions)
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
    {
        KernelJsonSchema? schema = null;

        // If no schema was provided but a type was provided, try to generate a schema from the type.
        if (parameterType is not null)
        {
            // Type must be usable as a generic argument to be used with JsonSchemaBuilder.
            bool invalidAsGeneric =
                // from RuntimeType.ThrowIfTypeNeverValidGenericArgument
#if NET_8_OR_GREATER
                parameterType.IsFunctionPointer ||
#endif
                parameterType.IsPointer ||
                parameterType.IsByRef ||
                parameterType == typeof(void);

            if (!invalidAsGeneric)
            {
                try
                {
                    if (InternalTypeConverter.ConvertToString(defaultValue) is string stringDefault && !string.IsNullOrWhiteSpace(stringDefault))
                    {
                        bool needsSpace = !string.IsNullOrWhiteSpace(description);
                        description += $"{(needsSpace ? " " : "")}(default value: {stringDefault})";
                    }

                    schema = KernelJsonSchemaBuilder.Build(null, parameterType, description);
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
                    // Register the handler for the 'System.ComponentModel.DescriptionAttribute' attribute to provide descriptions for .NET type members, such as fields and properties.
                    // See the Attributes section for more details - https://docs.json-everything.net/schema/schemagen/schema-generation/.
                    // This line must precede the JsonSchemaBuilder creation; otherwise, the registration will not take place.
                    AttributeHandler.AddHandler<DescriptionAttributeHandler>();

                    var builder = new JsonSchemaBuilder().FromType(parameterType);

                    if (!string.IsNullOrWhiteSpace(description))
                    {
                        builder = builder.Description(description!);
                    }
                    schema = new KernelJsonSchema(JsonSerializer.SerializeToElement(builder.Build()));
                    schema = jsonSerializerOptions is not null
                        ? KernelJsonSchemaBuilder.Build(parameterType, jsonSerializerOptions, description)
                        : KernelJsonSchemaBuilder.Build(parameterType, description);
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
                }
                catch (ArgumentException)
                {
                    // Invalid type; ignore, and leave schema as null.
                    // This should be exceedingly rare, as we checked for all known category of
                    // problematic types above. If it becomes more common that schema creation
                    // could fail expensively, we'll want to track whether inference was already
                    // attempted and avoid doing so on subsequent accesses if it was.
                }
            }
        }

        // Always return an instance so that subsequent reads of the Schema don't try to regenerate
        // it again. If inference failed, we just leave the Schema null in the instance.
        return new InitializedSchema { Inferred = true, Schema = schema };
    }

    /// <summary>A wrapper for a <see cref="KernelJsonSchema"/> and whether it was inferred or set explicitly by the user.</summary>
    internal sealed class InitializedSchema
    {
        /// <summary>true if the <see cref="Schema"/> was inferred; false if it was set explicitly by the user.</summary>
        public bool Inferred { get; set; }
        /// <summary>The schema, if one exists.</summary>
        public KernelJsonSchema? Schema { get; set; }
    }
}
