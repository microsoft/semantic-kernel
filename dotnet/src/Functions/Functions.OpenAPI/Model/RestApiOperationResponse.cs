// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Model;

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
    /// The schema against which the response body should be validated.
    /// </summary>
    public RestApiOperationResponseSchema? Schema { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="RestApiOperationResponse"/> class.
    /// </summary>
    /// <param name="content">The content of the response.</param>
    /// <param name="contentType">The content type of the response.</param>
    /// <param name="schema">The schema against which the response body should be validated.</param>
    public RestApiOperationResponse(object content, string contentType, RestApiOperationResponseSchema? schema = null)
    {
        this.Content = content;
        this.ContentType = contentType;
        this.Schema = schema;
    }

    /// <summary>
    /// Validates the response content against the schema.
    /// </summary>
    /// <returns>True if a schema is available and the content matches the schema. False otherwise.</returns>
    /// <remarks>
    /// If no schema is available, the response is considered valid.
    /// </remarks>
    public bool IsValid()
    {
        if (this.Schema is null)
        {
            return true;
        }

        return this.Schema.IsValid(this.Content.ToString()); // TODO -- is this correct thing to do with Content?
    }
}
