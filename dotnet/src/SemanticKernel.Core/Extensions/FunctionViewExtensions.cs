// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Extensions;

/// <summary>
/// Extensions for functions views.
/// </summary>
public static class FunctionViewExtensions
{
    private static readonly string s_successfulResponseCode = "200";
    private static readonly string s_successfulResponseDescription = "Success";

    /// <summary>
    /// Creates a <see cref="JsonSchemaFunctionManual"/> for a function.
    /// </summary>
    /// <param name="function">The function.</param>
    /// <param name="jsonSchemaDelegate">A delegate that creates a Json Schema from a <see cref="Type"/> and a semantic description.</param>
    /// <param name="includeOutputSchema">Indicates if the schema should include information about the output or return type of the function.</param>
    /// <returns></returns>
    public static async Task<JsonSchemaFunctionManual> ToJsonSchemaManualAsync(this FunctionView function, Func<Type, string, Task<JsonDocument>> jsonSchemaDelegate, bool includeOutputSchema = true)
    {
        var functionManual = new JsonSchemaFunctionManual
        {
            Name = function.Name,
            Description = function.Description,
        };

        var requiredProperties = new List<string>();
        foreach (var parameter in function.Parameters)
        {
            if (parameter.ParameterType != null)
            {
                functionManual.Parameters.Properties.Add(parameter.Name, await jsonSchemaDelegate(parameter.ParameterType, function.ReturnParameter.Description ?? "").ConfigureAwait(false));
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
            functionResponse.Description = s_successfulResponseDescription;

            if (function.ReturnParameter?.ParameterType != null)
            {
                functionResponse.Content.JsonResponse.Schema = await jsonSchemaDelegate(function.ReturnParameter.ParameterType, function.ReturnParameter.Description ?? "").ConfigureAwait(false);
            }
            else if (function.ReturnParameter?.Schema != null)
            {
                functionResponse.Content.JsonResponse.Schema = function.ReturnParameter.Schema;
            }

            functionManual.FunctionResponses.Add(s_successfulResponseCode, functionResponse);
        }

        return functionManual;
    }
}
