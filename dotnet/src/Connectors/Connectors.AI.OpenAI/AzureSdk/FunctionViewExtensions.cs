// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using Json.More;
using Json.Schema;
using Json.Schema.Generation;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Extensions for <see cref="FunctionView"/> specific to the OpenAI connector.
/// </summary>
public static class FunctionViewExtensions
{
    /// <summary>
    /// Convert a <see cref="FunctionView"/> to an <see cref="OpenAIFunction"/>.
    /// </summary>
    /// <param name="functionView">The <see cref="FunctionView"/> object to convert.</param>
    /// <returns>An <see cref="OpenAIFunction"/> object.</returns>
    public static OpenAIFunction ToOpenAIFunction(this FunctionView functionView)
    {
        var openAIParams = new List<OpenAIFunctionParameter>();
        foreach (ParameterView param in functionView.Parameters)
        {
            openAIParams.Add(new OpenAIFunctionParameter
            {
                Name = param.Name,
                Description = (param.Description ?? string.Empty)
                    + (string.IsNullOrEmpty(param.DefaultValue) ? string.Empty : $" (default value: {param.DefaultValue})"),
                Type = param.Type?.Name ?? "string",
                IsRequired = param.IsRequired ?? false,
                Schema = param.Schema ?? GetJsonSchemaDocument(param.ParameterType, param.Description),
            });
        }

        var returnParameter = new OpenAIFunctionReturnParameter
        {
            Description = functionView.ReturnParameter.Description ?? string.Empty,
            Schema = functionView.ReturnParameter.Schema ?? GetJsonSchemaDocument(functionView.ReturnParameter.ParameterType, functionView.ReturnParameter.Description),
        };

        return new OpenAIFunction
        {
            FunctionName = functionView.Name,
            PluginName = functionView.PluginName,
            Description = functionView.Description,
            Parameters = openAIParams,
            ReturnParameter = returnParameter
        };
    }

    /// <summary>
    /// Creates a <see cref="JsonDocument"/> that contains a Json Schema of the specified <see cref="Type"/> with the specified description.
    /// </summary>
    /// <param name="type">The object Type.</param>
    /// <param name="description">The object description.</param>
    /// <returns></returns>
    private static JsonDocument? GetJsonSchemaDocument(Type? type, string? description)
    {
        if (type == null)
        {
            return null;
        }

        var schemaDocument = new JsonSchemaBuilder()
                        .FromType(type)
                        .Description(description ?? string.Empty)
                        .Build()
                        .ToJsonDocument();

        return schemaDocument;
    }
}
