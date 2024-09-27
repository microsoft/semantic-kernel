// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Json.Schema;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Class for extensions methods for the <see cref="RestApiOperationResponse"/> class.
/// </summary>
public static class RestApiOperationResponseExtensions
{
    /// <summary>
    /// Validates the response content against the schema.
    /// </summary>
    /// <returns>True if the response is valid, false otherwise.</returns>
    /// <remarks>
    /// If the schema is not specified, the response is considered valid.
    /// If the content type is not specified, the response is considered valid.
    /// If the content type is not supported, the response is considered valid.
    /// Right now, only JSON is supported.
    /// </remarks>
    public static bool IsValid(this RestApiOperationResponse response)
    {
        if (response.ExpectedSchema is null)
        {
            return true;
        }

        if (string.IsNullOrEmpty(response.ContentType))
        {
            return true;
        }

        return response.ContentType switch
        {
            "application/json" => ValidateJson(response),
            "application/xml" => ValidateXml(response),
            "text/plain" or "text/html" => ValidateTextHtml(response),
            _ => true,
        };
    }

    private static bool ValidateJson(RestApiOperationResponse response)
    {
        try
        {
            var jsonSchema = JsonSchema.FromText(JsonSerializer.Serialize(response.ExpectedSchema));
            using var contentDoc = JsonDocument.Parse(response.Content.ToString());
            var result = jsonSchema.Evaluate(contentDoc);
            return result.IsValid;
        }
        catch (JsonException)
        {
            return false;
        }
    }

    private static bool ValidateXml(RestApiOperationResponse response)
    {
        // todo -- implement
        return true;
    }

    private static bool ValidateTextHtml(RestApiOperationResponse response)
    {
        try
        {
            var jsonSchema = JsonSchema.FromText(JsonSerializer.Serialize(response.ExpectedSchema));
            using var contentDoc = JsonDocument.Parse($"\"{response.Content}\"");
            var result = jsonSchema.Evaluate(contentDoc);
            return result.IsValid;
        }
        catch (JsonException)
        {
            return false;
        }
    }
}
