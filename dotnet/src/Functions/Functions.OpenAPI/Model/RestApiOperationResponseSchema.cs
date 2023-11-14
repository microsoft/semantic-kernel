// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Newtonsoft.Json.Linq;
using Newtonsoft.Json.Schema;

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
    /// Properties of the schema, applicable if the schema is an object.
    /// </summary>
    [JsonPropertyName("properties")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IDictionary<string, RestApiOperationResponseSchema> Properties { get; set; }

    /// <summary>
    /// Items schema, applicable if the schema is an array.
    /// </summary>
    [JsonPropertyName("items")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public RestApiOperationResponseSchema? Items { get; set; }

    // You can add additional fields as necessary, such as Format, Enum, etc.

    /// <summary>
    /// Initializes a new instance of the <see cref="RestApiOperationResponseSchema"/> class.
    /// </summary>
    public RestApiOperationResponseSchema(
        string? title = null,
        string? type = null,
        IDictionary<string, RestApiOperationResponseSchema>? properties = null,
        RestApiOperationResponseSchema? items = null)
    {
        this.Title = title;
        this.Type = type;
        this.Properties = properties ?? new Dictionary<string, RestApiOperationResponseSchema>();
        this.Items = items;
    }

    /// <summary>
    /// Validates the content against the schema.
    /// </summary>
    /// <param name="content">The content to validate.</param>
    /// <returns>True if the content matches the schema. False otherwise.</returns>
    public bool Validate(string content) // object or string?
    {
        if (this.Type == null)
        {
            return true;
        }
        else
        {
            if (this.Type == "object")
            {
                var contentJson = JsonDocument.Parse(content);

                return JObject.Parse(content).IsValid(JSchema.Parse(JsonSerializer.Serialize(this)), out IList<string> _);
            }

            return false;
        }
    }
}
