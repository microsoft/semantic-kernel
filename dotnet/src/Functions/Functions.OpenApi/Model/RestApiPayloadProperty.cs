// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// REST API payload property.
/// </summary>
[Experimental("SKEXP0040")]
public sealed class RestApiPayloadProperty
{
    /// <summary>
    /// The property name.
    /// </summary>
    public string Name { get; }

    /// <summary>
    /// The property type.
    /// </summary>
    internal string Type { get; }

    /// <summary>
    /// The property type modifier that refines the generic parameter type to a more specific one.
    /// More details can be found at https://swagger.io/docs/specification/data-models/data-types
    /// </summary>
    public string? Format { get; }

    /// <summary>
    /// The property description.
    /// </summary>
    public string? Description { get; }

    /// <summary>
    /// Flag specifying if the property is required or not.
    /// </summary>
    public bool IsRequired { get; }

    /// <summary>
    /// The properties.
    /// </summary>
    public IReadOnlyList<RestApiPayloadProperty> Properties { get; }

    /// <summary>
    /// The schema of the parameter.
    /// </summary>
    public KernelJsonSchema? Schema { get; }

    /// <summary>
    /// The default value.
    /// </summary>
    public object? DefaultValue { get; }

    /// <summary>
    /// Creates an instance of a <see cref="RestApiPayloadProperty"/> class.
    /// </summary>
    /// <param name="name">The name of the property.</param>
    /// <param name="type">The type of the property.</param>
    /// <param name="isRequired">A flag specifying if the property is required or not.</param>
    /// <param name="properties">A list of properties for the payload property.</param>
    /// <param name="description">A description of the property.</param>
    /// <param name="format">The parameter type modifier that refines the generic parameter type to a more specific one.
    /// More details can be found at https://swagger.io/docs/specification/data-models/data-types</param>
    /// <param name="schema">The schema of the payload property.</param>
    /// <param name="defaultValue">The default value of the property.</param>
    /// <returns>Returns a new instance of the <see cref="RestApiPayloadProperty"/> class.</returns>
    internal RestApiPayloadProperty(
        string name,
        string type,
        bool isRequired,
        IReadOnlyList<RestApiPayloadProperty> properties,
        string? description = null,
        string? format = null,
        KernelJsonSchema? schema = null,
        object? defaultValue = null)
    {
        this.Name = name;
        this.Type = type;
        this.IsRequired = isRequired;
        this.Description = description;
        this.Properties = properties;
        this.Schema = schema;
        this.Format = format;
        this.DefaultValue = defaultValue;
    }
}
