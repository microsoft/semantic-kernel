// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Json.Schema;

namespace Microsoft.SemanticKernel.Planners.Model;

internal class JsonSchemaFunctionManual
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("parameters")]
    public OpenAiObjectType Parameters { get; set; } = new OpenAiObjectType();

    [JsonPropertyName("responses")]
    public Dictionary<string, FunctionResponse> FunctionResponses { get; set; } = new Dictionary<string, FunctionResponse> { };
}

internal class OpenAiObjectType
{
    [JsonPropertyName("type")]
    public string Type => "object";

    [JsonPropertyName("required")]
    public List<string> Required { get; set; } = new List<string>();

    [JsonPropertyName("properties")]
    public Dictionary<string, JsonDocument> Properties { get; set; } = new Dictionary<string, JsonDocument> { };
}

public class FunctionResponse
{
    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("content")]
    public JsonFunctionContent Content { get; set; } = new JsonFunctionContent();
}

public class JsonFunctionContent
{
    [JsonPropertyName("application/json")]
    public JsonSchemaWrapper JsonSchemaWrapper { get; } = new JsonSchemaWrapper();
}

public class JsonSchemaWrapper
{
    [JsonPropertyName("schema")]
    public JsonDocument? Schema { get; set; }
}
