// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Collections.ObjectModel;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// REST API payload.
/// </summary>
public sealed class RestApiPayload
{
    /// <summary>
    /// The payload MediaType.
    /// </summary>
    public string MediaType { get; }

    /// <summary>
    /// The payload description.
    /// </summary>
    public string? Description { get; }

    /// <summary>
    /// The payload properties.
    /// </summary>
    public IList<RestApiPayloadProperty> Properties { get; private set; }

    /// <summary>
    /// The schema of the parameter.
    /// </summary>
    public KernelJsonSchema? Schema { get; }

    /// <summary>
    /// Creates an instance of a <see cref="RestApiPayload"/> class.
    /// </summary>
    /// <param name="mediaType">The media type.</param>
    /// <param name="properties">The properties.</param>
    /// <param name="description">The description.</param>
    /// <param name="schema">The JSON Schema.</param>
    internal RestApiPayload(string mediaType, IList<RestApiPayloadProperty> properties, string? description = null, KernelJsonSchema? schema = null)
    {
        this.MediaType = mediaType;
        this.Properties = properties;
        this.Description = description;
        this.Schema = schema;
    }

    /// <summary>
    /// Makes the current instance unmodifiable.
    /// </summary>
    internal void Freeze()
    {
        this.Properties = new ReadOnlyCollection<RestApiPayloadProperty>(this.Properties);
        foreach (var property in this.Properties)
        {
            property.Freeze();
        }
    }
}
