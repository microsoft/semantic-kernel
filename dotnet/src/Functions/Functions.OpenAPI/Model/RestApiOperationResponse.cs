// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Text.Json;
using Json.Schema;

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
    /// The schema of the response.
    /// </summary>
    public JsonDocument? Schema { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="RestApiOperationResponse"/> class.
    /// </summary>
    /// <param name="content">The content of the response.</param>
    /// <param name="contentType">The content type of the response.</param>
    /// <param name="schema">The schema against which the response body should be validated.</param>
    public RestApiOperationResponse(object content, string contentType, JsonDocument? schema = null)
    {
        this.Content = content;
        this.ContentType = contentType;
        this.Schema = schema;
    }

    /// <summary>
    /// Validates the response content against the schema.
    /// </summary>
    /// <returns>True if the response is valid, false otherwise.</returns>
    /// <remarks>
    /// If the schema is not specified, the response is considered valid.
    /// </remarks>
    public bool IsValid()
    {
        if (this.Schema is null)
        {
            return true;
        }

        var jsonSchema = JsonSchema.FromText(JsonSerializer.Serialize(this.Schema));

        try
        {
            var contentDoc = JsonDocument.Parse(this.Content.ToString());
            var result = jsonSchema.Evaluate(contentDoc);
            return result.IsValid;
        }
        catch (JsonException)
        {
            return false;
        }
    }
}
