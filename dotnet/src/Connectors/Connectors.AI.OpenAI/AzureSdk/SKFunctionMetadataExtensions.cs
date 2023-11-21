// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Extensions for <see cref="SKFunctionMetadata"/> specific to the OpenAI connector.
/// </summary>
public static class SKFunctionMetadataExtensions
{
    /// <summary>
    /// Convert a <see cref="SKFunctionMetadata"/> to an <see cref="OpenAIFunction"/>.
    /// </summary>
    /// <param name="metadata">The <see cref="SKFunctionMetadata"/> object to convert.</param>
    /// <returns>An <see cref="OpenAIFunction"/> object.</returns>
    public static OpenAIFunction ToOpenAIFunction(this SKFunctionMetadata metadata)
    {
        var openAIParams = new List<OpenAIFunctionParameter>();
        foreach (SKParameterMetadata param in metadata.Parameters)
        {
            // Get the parameter's schema, or if it doesn't have one but it has a .NET type,
            // infer the schema from the .NET type.
            SKJsonSchema? schema = param.Schema ?? OpenAIFunction.GetJsonSchema(param.ParameterType, param.Description);

            // Read the "type" property from the schema, if it exists.
            // If it doesn't, that means we lack any type information for the property.
            string? type = null;
            if (schema?.RootElement.TryGetProperty("type", out JsonElement prop) == true)
            {
                type = prop.GetString();
            }
            type ??= "string";

            string description = string.IsNullOrEmpty(param.DefaultValue) ?
                param.Description :
                $"{param.Description} (default value: {param.DefaultValue})";

            openAIParams.Add(new OpenAIFunctionParameter
            {
                Name = param.Name,
                Description = description,
                IsRequired = param.IsRequired,
                ParameterType = param.ParameterType,
                Schema = schema,
            });
        }

        return new OpenAIFunction
        {
            FunctionName = metadata.Name,
            PluginName = metadata.PluginName ?? "",
            Description = metadata.Description,
            Parameters = openAIParams,
            ReturnParameter = new OpenAIFunctionReturnParameter
            {
                Description = metadata.ReturnParameter.Description,
                ParameterType = metadata.ReturnParameter.ParameterType,
                Schema = metadata.ReturnParameter.Schema ?? OpenAIFunction.GetJsonSchema(metadata.ReturnParameter.ParameterType, metadata.ReturnParameter.Description),
            }
        };
    }
}
