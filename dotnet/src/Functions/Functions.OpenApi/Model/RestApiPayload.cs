// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// REST API payload.
/// </summary>
[Experimental("SKEXP0040")]
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
    public IReadOnlyList<RestApiPayloadProperty> Properties { get; }

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
    internal RestApiPayload(string mediaType, IReadOnlyList<RestApiPayloadProperty> properties, string? description = null, KernelJsonSchema? schema = null)
    {
        this.MediaType = mediaType;
        this.Properties = properties;
        this.Description = description;
        this.Schema = schema;
    }
}
