﻿// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// The REST API operation parameter.
/// </summary>
public sealed class RestApiOperationParameter
{
    /// <summary>
    /// The parameter name.
    /// </summary>
    public string Name { get; }

    /// <summary>
    /// The property alternative name. It can be used as an alternative name in contexts where the original name can't be used.
    /// </summary>
    public string? AlternativeName { get; set; }

    /// <summary>
    /// The parameter type - string, integer, number, boolean, array and object.
    /// </summary>
    public string Type { get; }

    /// <summary>
    /// The parameter type modifier that refines the generic parameter type to a more specific one.
    /// More details can be found at https://swagger.io/docs/specification/data-models/data-types
    /// </summary>
    public string? Format { get; }

    /// <summary>
    /// The parameter description.
    /// </summary>
    public string? Description { get; }

    /// <summary>
    /// Flag specifying if the parameter is required or not.
    /// </summary>
    public bool IsRequired { get; }

    /// <summary>
    /// The parameter location.
    /// </summary>
    public RestApiOperationParameterLocation Location { get; }

    /// <summary>
    /// The parameter style - defines how multiple values are delimited.
    /// </summary>
    public RestApiOperationParameterStyle? Style { get; }

    /// <summary>
    /// Type of array item for parameters of "array" type.
    /// </summary>
    public string? ArrayItemType { get; }

    /// <summary>
    /// The default value.
    /// </summary>
    public object? DefaultValue { get; }

    /// <summary>
    /// Specifies whether arrays and objects should generate separate parameters for each array item or object property.
    /// </summary>
    public bool Expand { get; }

    /// <summary>
    /// The schema of the parameter.
    /// </summary>
    public KernelJsonSchema? Schema { get; }

    /// <summary>
    /// Creates an instance of a <see cref="RestApiOperationParameter"/> class.
    /// </summary>
    /// <param name="name">The parameter name.</param>
    /// <param name="type">The parameter type.</param>
    /// <param name="isRequired">Flag specifying if the parameter is required or not.</param>
    /// <param name="expand">Specifies whether arrays and objects should generate separate parameters for each array item or object property.</param>
    /// <param name="location">The parameter location.</param>
    /// <param name="style">The parameter style - defines how multiple values are delimited.</param>
    /// <param name="arrayItemType">Type of array item for parameters of "array" type.</param>
    /// <param name="defaultValue">The parameter default value.</param>
    /// <param name="description">The parameter description.</param>
    /// <param name="format">The parameter type modifier that refines the generic parameter type to a more specific one.
    /// More details can be found at https://swagger.io/docs/specification/data-models/data-types</param>
    /// <param name="schema">The parameter schema.</param>
    public RestApiOperationParameter(
        string name,
        string type,
        bool isRequired,
        bool expand,
        RestApiOperationParameterLocation location,
        RestApiOperationParameterStyle? style = null,
        string? arrayItemType = null,
        object? defaultValue = null,
        string? description = null,
        string? format = null,
        KernelJsonSchema? schema = null)
    {
        this.Name = name;
        this.Type = type;
        this.IsRequired = isRequired;
        this.Expand = expand;
        this.Location = location;
        this.Style = style;
        this.ArrayItemType = arrayItemType;
        this.DefaultValue = defaultValue;
        this.Description = description;
        this.Format = format;
        this.Schema = schema;
    }
}
