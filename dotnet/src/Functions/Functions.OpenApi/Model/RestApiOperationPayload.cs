// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// The REST API operation payload.
/// </summary>
[Experimental("SKEXP0040")]
public sealed class RestApiOperationPayload
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
    public IReadOnlyList<RestApiOperationPayloadProperty> Properties { get; }

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
    internal RestApiOperationPayload(string mediaType, IReadOnlyList<RestApiOperationPayloadProperty> properties, string? description = null, KernelJsonSchema? schema = null)
    {
        this.MediaType = mediaType;
        this.Properties = properties;
        this.Description = description;
        this.Schema = schema;
    }
}
