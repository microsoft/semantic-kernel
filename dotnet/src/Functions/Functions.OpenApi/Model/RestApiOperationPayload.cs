// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// The REST API operation payload.
/// </summary>
public class RestApiOperationPayload
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
    public IList<RestApiOperationPayloadProperty> Properties { get; }

    /// <summary>
    /// The schema of the parameter.
    /// </summary>
    public KernelJsonSchema? Schema { get; }

    /// <summary>
    /// Creates an instance of a <see cref="RestApiOperationPayload"/> class.
    /// </summary>
    /// <param name="mediaType">The media type.</param>
    /// <param name="properties">The properties.</param>
    /// <param name="description">The description.</param>
    /// <param name="schema">The JSON Schema.</param>
    public RestApiOperationPayload(string mediaType, IList<RestApiOperationPayloadProperty> properties, string? description = null, KernelJsonSchema? schema = null)
    {
        this.MediaType = mediaType;
        this.Properties = properties;
        this.Description = description;
        this.Schema = schema;
    }
}
