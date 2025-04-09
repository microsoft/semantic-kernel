// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// The REST API operation response.
/// </summary>
[TypeConverterAttribute(typeof(RestApiOperationResponseConverter))]
public sealed class RestApiOperationResponse
{
    /// <summary>
    /// Gets the content of the response.
    /// </summary>
    public object? Content { get; set; }

    /// <summary>
    /// Gets the content type of the response.
    /// </summary>
    public string? ContentType { get; }

    /// <summary>
    /// The expected schema of the response as advertised in the OpenAPI operation.
    /// </summary>
    public KernelJsonSchema? ExpectedSchema { get; set; }

    /// <summary>
    /// Gets the method used for the HTTP request.
    /// </summary>
    public string? RequestMethod { get; init; }

    /// <summary>
    /// Gets the System.Uri used for the HTTP request.
    /// </summary>
    public Uri? RequestUri { get; init; }

    /// <summary>
    /// Gets the payload sent in the request.
    /// </summary>
    public object? RequestPayload { get; init; }

    /// <summary>
    /// The response headers.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IDictionary<string, IEnumerable<string>>? Headers { get; set; }

    /// <summary>
    /// Gets a dictionary for ambient data associated with the response.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IDictionary<string, object?>? Data { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="RestApiOperationResponse"/> class.
    /// </summary>
    /// <param name="content">The content of the response.</param>
    /// <param name="contentType">The content type of the response.</param>
    /// <param name="expectedSchema">The schema against which the response body should be validated.</param>
    public RestApiOperationResponse(object? content, string? contentType, KernelJsonSchema? expectedSchema = null)
    {
        this.Content = content;
        this.ContentType = contentType;
        this.ExpectedSchema = expectedSchema;
    }

    /// <inheritdoc/>
    public override string ToString() => this.Content?.ToString() ?? string.Empty;
}
