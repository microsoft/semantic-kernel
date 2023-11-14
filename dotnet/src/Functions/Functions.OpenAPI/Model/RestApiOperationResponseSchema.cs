// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;
using Json.Schema;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Model;

/// <summary>
/// The REST API operation response schema
/// </summary>
public sealed class RestApiOperationResponseSchema
{
    /// <summary>
    /// The title of the schema.
    /// </summary>
    [JsonPropertyName("title")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Title { get; set; }

    /// <summary>
    /// The type of the schema (e.g., object, array, string, integer).
    /// </summary>
    [JsonPropertyName("type")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Type { get; set; }

    /// <summary>
    /// The schema of the response.
    /// </summary>
    public JsonDocument? Schema { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="RestApiOperationResponseSchema"/> class.
    /// </summary>
    public RestApiOperationResponseSchema(
        string? title = null,
        string? type = null,
        JsonDocument? schema = null)
    {
        this.Title = title;
        this.Type = type;
        this.Schema = schema;
    }

    /// <summary>
    /// Validates the content against the schema.
    /// </summary>
    /// <param name="content">The content to validate.</param>
    /// <returns>True if the content matches the schema. False otherwise.</returns>
    public bool IsValid(string content) // object or string?
    {
        if (this.Type == null)
        {
            return true;
        }

        var jsonSchema = Json.Schema.JsonSchema.FromText(JsonSerializer.Serialize(this.Schema));

        try
        {
            var contentDoc = JsonDocument.Parse(content);
            var result = jsonSchema.Evaluate(contentDoc);
            return result.IsValid;
        }
        catch (JsonException)
        {
            return false;
        }
    }
}
