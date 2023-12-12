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
    /// Creates an instance of a <see cref="RestApiOperationPayloadProperty"/> class.
    /// </summary>
    /// <param name="name">Property name.</param>
    /// <param name="type">Property type.</param>
    /// <param name="isRequired">Flag specifying if the property is required or not.</param>
    /// <param name="properties">Properties.</param>
    /// <param name="description">Property description.</param>
    /// <param name="schema">The schema of the payload property.</param>
    public RestApiOperationPayloadProperty(
        string name,
        string type,
        bool isRequired,
        IList<RestApiOperationPayloadProperty> properties,
        string? description = null,
        KernelJsonSchema? schema = null)
    {
        this.Name = name;
        this.Type = type;
        this.IsRequired = isRequired;
        this.Description = description;
        this.Properties = properties;
        this.Schema = schema;
    }
}
