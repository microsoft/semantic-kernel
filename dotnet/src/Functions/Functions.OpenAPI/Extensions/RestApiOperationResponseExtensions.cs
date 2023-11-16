// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Json.Schema;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Functions.OpenAPI.Model;
#pragma warning restore IDE0130

/// <summary>
/// Class for extensions methods for the <see cref="RestApiOperation"/> class.
/// </summary>
public static class RestApiOperationResponseExtensions
{
    /// <summary>
    /// Validates the response content against the schema.
    /// </summary>
    /// <returns>True if the response is valid, false otherwise.</returns>
    /// <remarks>
    /// If the schema is not specified, the response is considered valid.
    /// </remarks>
    public static bool IsValid(this RestApiOperationResponse response)
    {
        if (response.ExpectedSchema is null)
        {
            return true;
        }

        var jsonSchema = JsonSchema.FromText(JsonSerializer.Serialize(response.ExpectedSchema));

        try
        {
            var contentDoc = JsonDocument.Parse(response.Content.ToString());
            var result = jsonSchema.Evaluate(contentDoc);
            return result.IsValid;
        }
        catch (JsonException)
        {
            return false;
        }
    }
}
