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

    // Optional: Method to validate the response content against the schema
    public bool ValidateResponse()
    {
        // Implement validation logic here
        // Return true if validation passes, false otherwise
        return true;
    }
}
