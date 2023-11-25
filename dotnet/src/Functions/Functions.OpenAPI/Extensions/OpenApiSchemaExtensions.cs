// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text;
using Microsoft.OpenApi.Models;
using Microsoft.OpenApi.Writers;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;

internal static class OpenApiSchemaExtensions
{
    /// <summary>
    /// Gets a JSON serialized representation of an <see cref="OpenApiSchema"/>
    /// </summary>
    /// <param name="schema">The schema.</param>
    /// <returns>An instance of <see cref="KernelParameterJsonSchema"/> that contains the JSON Schema.</returns>
    internal static KernelParameterJsonSchema ToJsonSchema(this OpenApiSchema schema)
    {
        var schemaBuilder = new StringBuilder();
        var jsonWriter = new OpenApiJsonWriter(new StringWriter(schemaBuilder));
        jsonWriter.Settings.InlineLocalReferences = true;
        schema.SerializeAsV3(jsonWriter);
        return KernelParameterJsonSchema.Parse(schemaBuilder.ToString());
    }
}
