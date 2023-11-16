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
    /// Creates a <see cref="JsonSchemaFunctionManual"/> for a function.
    /// </summary>
    /// <param name="function">The function.</param>
    /// <param name="jsonSchemaDelegate">A delegate that creates a Json Schema from a <see cref="Type"/> and a semantic description.</param>
    /// <param name="includeOutputSchema">Indicates if the schema should include information about the output or return type of the function.</param>
    /// <returns>An instance of <see cref="JsonSchemaFunctionManual"/></returns>
    public static JsonSchemaFunctionManual ToJsonSchemaManual(this FunctionView function, Func<Type, string, JsonDocument> jsonSchemaDelegate, bool includeOutputSchema = true)
    {
        var functionManual = new JsonSchemaFunctionManual
        {
            Name = $"{function.PluginName}_{function.Name}",
            Description = function.Description,
        };

        var requiredProperties = new List<string>();
        foreach (var parameter in function.Parameters)
        {
            if (parameter.ParameterType != null)
            {
                functionManual.Parameters.Properties.Add(parameter.Name, jsonSchemaDelegate(parameter.ParameterType, parameter.Description ?? ""));
                if (parameter.IsRequired ?? false)
                {
                    requiredProperties.Add(parameter.Name);
                }
            }
            else if (parameter.Schema != null)
            {
                functionManual.Parameters.Properties.Add(parameter.Name, parameter.Schema);
                if (parameter.IsRequired ?? false)
                {
                    requiredProperties.Add(parameter.Name);
                }
            }
        }

        if (includeOutputSchema)
        {
            var functionResponse = new JsonSchemaFunctionResponse();
            functionResponse.Description = SuccessfulResponseDescription;

            if (function.ReturnParameter?.ParameterType != null)
            {
                functionResponse.Content.JsonResponse.Schema = jsonSchemaDelegate(function.ReturnParameter.ParameterType, function.ReturnParameter.Description ?? "");
            }
            else if (function.ReturnParameter?.Schema != null)
            {
                functionResponse.Content.JsonResponse.Schema = function.ReturnParameter.Schema;
            }

            functionManual.FunctionResponses.Add(SuccessfulResponseCode, functionResponse);
        }

        functionManual.Parameters.Required = requiredProperties;
        return functionManual;
    }
}
