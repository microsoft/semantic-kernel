// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Model;

/// <summary>
/// The REST API operation response.
/// </summary>
public sealed class RestApiOperationResponse
{
    /// <summary>
    /// Gets the content of the response.
    /// </summary>
    [JsonPropertyName("content")]
    public string Content { get; }

    /// <summary>
    /// Gets the content type of the response.
    /// </summary>
    [JsonPropertyName("contentType")]
    public string ContentType { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="RestApiOperationResponse"/> class.
    /// </summary>
    /// <param name="content">The content of the response.</param>
    /// <param name="contentType">The content type of the response.</param>
    public RestApiOperationResponse(string content, string contentType)
    {
        this.Content = content;
        this.ContentType = contentType;
    }
}
