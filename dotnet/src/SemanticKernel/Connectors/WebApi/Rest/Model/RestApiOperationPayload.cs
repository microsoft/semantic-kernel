// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.WebApi.Rest.Model;

/// <summary>
/// The REST API operation payload.
/// </summary>
internal record RestApiOperationPayload
{
    /// <summary>
    /// The payload MediaType.
    /// </summary>
    public string MediaType { get; }

    /// <summary>
    /// The payload properties. 
    /// </summary>
    public IList<RestApiOperationPayloadProperty> Properties { get; }

    /// <summary>
    /// Creates an instance of a <see cref="RestApiOperationPayload"/> class.
    /// </summary>
    /// <param name="mediaType">The media type.</param>
    /// <param name="properties">The properties.</param>
    public RestApiOperationPayload(string mediaType, IList<RestApiOperationPayloadProperty> properties)
    {
        this.MediaType = mediaType;
        this.Properties = properties;
    }
}
