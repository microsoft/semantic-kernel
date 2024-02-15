// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// The REST API operation payload property.
/// </summary>
public sealed class RestApiOperationPayloadProperty
{
    /// <summary>
    /// The property name.
    /// </summary>
    public string Name { get; }

    /// <summary>
    /// The property type.
    /// </summary>
    public string Type { get; }

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
    public IList<RestApiOperationPayloadProperty> Properties { get; }

    /// <summary>
    /// The schema of the parameter.
    /// </summary>
    public KernelJsonSchema? Schema { get; }

    /// <summary>
    /// The default value.
    /// </summary>
    public object? DefaultValue { get; }

    /// <summary>
    /// Creates an instance of a <see cref="RestApiOperationPayloadProperty"/> class.
    /// </summary>
    /// <param name="name">The name of the property.</param>
    /// <param name="type">The type of the property.</param>
    /// <param name="isRequired">A flag specifying if the property is required or not.</param>
    /// <param name="properties">A list of properties for the payload property.</param>
    /// <param name="description">A description of the property.</param>
    /// <param name="schema">The schema of the payload property.</param>
    /// <param name="defaultValue">The default value of the property.</param>
    /// <returns>Returns a new instance of the <see cref="RestApiOperationPayloadProperty"/> class.</returns>
    public RestApiOperationPayloadProperty(
        string name,
        string type,
        bool isRequired,
        IList<RestApiOperationPayloadProperty> properties,
        string? description = null,
        KernelJsonSchema? schema = null,
        object? defaultValue = null)
    {
        this.Name = name;
        this.Type = type;
        this.IsRequired = isRequired;
        this.Description = description;
        this.Properties = properties;
        this.Schema = schema;
        this.DefaultValue = defaultValue;
    }
}
