// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// REST API response.
/// </summary>
public sealed class RestApiExpectedResponse
{
    /// <summary>
    /// Gets the description of the response.
    /// </summary>
    public string Description { get; }

    /// <summary>
    /// Gets the media type of the response.
    /// </summary>
    public string MediaType { get; }

    /// <summary>
    /// The schema of the response.
    /// </summary>
    public KernelJsonSchema? Schema { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="RestApiExpectedResponse"/> class.
    /// </summary>
    /// <param name="description">The description of the response.</param>
    /// <param name="mediaType">The media type of the response.</param>
    /// <param name="schema">The schema against which the response body should be validated.</param>
    internal RestApiExpectedResponse(string description, string mediaType, KernelJsonSchema? schema = null)
    {
        this.Description = description;
        this.MediaType = mediaType;
        this.Schema = schema;
    }
}
