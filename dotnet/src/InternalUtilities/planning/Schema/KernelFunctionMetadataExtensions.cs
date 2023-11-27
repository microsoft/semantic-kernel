// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Extensions for function metadata.
/// </summary>
internal static class KernelFunctionMetadataExtensions
{
    private const string SuccessfulResponseCode = "200";
    private const string SuccessfulResponseDescription = "Success";

    /// <summary>
    /// Creates a <see cref="JsonSchemaFunctionView"/> for a function.
    /// </summary>
    /// <param name="function">The function.</param>
    /// <param name="jsonSchemaDelegate">A delegate that creates a JSON Schema from a <see cref="Type"/> and a semantic description.</param>
    /// <param name="includeOutputSchema">Indicates if the schema should include information about the output or return type of the function.</param>
    /// <returns>An instance of <see cref="JsonSchemaFunctionView"/></returns>
    public static JsonSchemaFunctionView ToJsonSchemaFunctionView(this KernelFunctionMetadata function, Func<Type?, string?, KernelJsonSchema?> jsonSchemaDelegate, bool includeOutputSchema = true)
    {
        var functionView = new JsonSchemaFunctionView
        {
            Name = $"{function.PluginName}_{function.Name}",
            Description = function.Description,
        };

        var requiredProperties = new List<string>();
        foreach (var parameter in function.Parameters)
        {
            var schema = parameter.Schema ?? jsonSchemaDelegate(parameter.ParameterType, parameter.Description);
            if (schema is not null)
            {
                functionView.Parameters.Properties.Add(parameter.Name, schema);
            }
            if (parameter.IsRequired)
            {
                requiredProperties.Add(parameter.Name);
            }
        }

        if (includeOutputSchema)
        {
            var functionResponse = new JsonSchemaFunctionResponse
            {
                Description = SuccessfulResponseDescription
            };

            var schema = function.ReturnParameter.Schema ?? jsonSchemaDelegate(function.ReturnParameter.ParameterType, SuccessfulResponseDescription);
            functionResponse.Content.JsonResponse.Schema = schema;

            functionView.FunctionResponses.Add(SuccessfulResponseCode, functionResponse);
        }

        functionView.Parameters.Required = requiredProperties;
        return functionView;
    }
}
