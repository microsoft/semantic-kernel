// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// The REST API operation response.
/// </summary>
[TypeConverterAttribute(typeof(RestApiOperationResponseConverter))]
public sealed class RestApiOperationResponse
{
    /// <summary>
    /// Gets the content of the response.
    /// </summary>
    public object Content { get; }

    /// <summary>
    /// Gets the content type of the response.
    /// </summary>
    public string ContentType { get; }

    /// <summary>
    /// The expected schema of the response as advertised in the OpenAPI operation.
    /// </summary>
    public KernelJsonSchema? ExpectedSchema { get; internal set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="RestApiOperationResponse"/> class.
    /// </summary>
    /// <param name="content">The content of the response.</param>
    /// <param name="contentType">The content type of the response.</param>
    /// <param name="expectedSchema">The schema against which the response body should be validated.</param>
    public RestApiOperationResponse(object content, string contentType, KernelJsonSchema? expectedSchema = null)
    {
        this.Content = content;
        this.ContentType = contentType;
        this.ExpectedSchema = expectedSchema;
    }

    /// <inheritdoc/>
    public override string ToString() => this.Content?.ToString() ?? string.Empty;
}
