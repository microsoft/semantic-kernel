// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text;
using System.Text.Json;
using Microsoft.OpenApi.Models;
using Microsoft.OpenApi.Writers;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;
internal static class OpenApiSchemaExtensions
{
    /// <summary>
    /// Gets a JSON serialized representation of an <see cref="OpenApiSchema"/>
    /// </summary>
    /// <param name="schema">The schema.</param>
    /// <returns>An instance of <see cref="JsonDocument"/> that contains the Json Schema.</returns>
    internal static JsonDocument ToJsonDocument(this OpenApiSchema schema)
    {
        var schemaBuilder = new StringBuilder();
        var jsonWriter = new OpenApiJsonWriter(new StringWriter(schemaBuilder));
        jsonWriter.Settings.InlineLocalReferences = true;
        schema.SerializeAsV3(jsonWriter);
        return JsonDocument.Parse(schemaBuilder.ToString());
    }
}
