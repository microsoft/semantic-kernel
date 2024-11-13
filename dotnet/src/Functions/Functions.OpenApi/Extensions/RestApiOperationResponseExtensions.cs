// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Json.Schema;

namespace Microsoft.SemanticKernel;

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

        return response.ContentType! switch
        {
            var ct when ct.StartsWith("application/json", StringComparison.OrdinalIgnoreCase) => ValidateJson(response),
            var ct when ct.StartsWith("application/xml", StringComparison.OrdinalIgnoreCase) => ValidateXml(response),
            var ct when ct.StartsWith("text/plain", StringComparison.OrdinalIgnoreCase) || ct.StartsWith("text/html", StringComparison.OrdinalIgnoreCase) => ValidateTextHtml(response),
            _ => true,
        };
    }

    private static bool ValidateJson(RestApiOperationResponse response)
    {
        try
        {
            var jsonSchema = JsonSchema.FromText(JsonSerializer.Serialize(response.ExpectedSchema));
            using var contentDoc = JsonDocument.Parse(response.Content?.ToString() ?? string.Empty);
            var result = jsonSchema.Evaluate(contentDoc);
            return result.IsValid;
        }
        catch (JsonException)
        {
            return false;
        }
    }

    private static bool ValidateXml(RestApiOperationResponse _)
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
