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
    /// <returns></returns>
    internal static JsonDocument GetSchemaDocument(this OpenApiSchema schema)
    {
        var schemaBuilder = new StringBuilder();
        schema.SerializeAsV3WithoutReference(new OpenApiJsonWriter(new StringWriter(schemaBuilder)));
        return JsonDocument.Parse(schemaBuilder.ToString());
    }
}
