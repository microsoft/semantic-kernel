// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Extensions;

/// <summary>
/// Extensions for functions views.
/// </summary>
public static class FunctionViewExtensions
{
    private const string SuccessfulResponseCode = "200";
    private const string SuccessfulResponseDescription = "Success";

    /// <summary>
    /// Creates a <see cref="JsonSchemaFunctionView"/> for a function.
    /// </summary>
    /// <param name="function">The function.</param>
    /// <param name="jsonSchemaDelegate">A delegate that creates a Json Schema from a <see cref="Type"/> and a semantic description.</param>
    /// <param name="includeOutputSchema">Indicates if the schema should include information about the output or return type of the function.</param>
    /// <returns>An instance of <see cref="JsonSchemaFunctionView"/></returns>
    public static JsonSchemaFunctionView ToJsonSchemaFunctionView(this FunctionView function, Func<Type?, string?, JsonDocument?> jsonSchemaDelegate, bool includeOutputSchema = true)
    {
        var functionView = new JsonSchemaFunctionView
        {
            Name = $"{function.PluginName}_{function.Name}",
            Description = function.Description,
        };

        var requiredProperties = new List<string>();
        foreach (var parameter in function.Parameters)
        {
            var schema = parameter.Schema ?? jsonSchemaDelegate(parameter.ParameterType, parameter.Description ?? string.Empty);
            if (schema is not null)
            {
                functionView.Parameters.Properties.Add(parameter.Name, schema);
            }
            if (parameter.IsRequired ?? false)
            {
                requiredProperties.Add(parameter.Name);
            }
        }

        if (includeOutputSchema)
        {
            var functionResponse = new JsonSchemaFunctionResponse();
            functionResponse.Description = SuccessfulResponseDescription;

            var schema = function.ReturnParameter.Schema ?? jsonSchemaDelegate(function.ReturnParameter.ParameterType!, SuccessfulResponseDescription);
            functionResponse.Content.JsonResponse.Schema = schema;

            functionView.FunctionResponses.Add(SuccessfulResponseCode, functionResponse);
        }

        functionView.Parameters.Required = requiredProperties;
        return functionView;
    }
}
