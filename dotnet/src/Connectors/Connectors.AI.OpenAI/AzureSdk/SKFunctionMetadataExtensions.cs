// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Extensions for <see cref="SKFunctionMetadata"/> specific to the OpenAI connector.
/// </summary>
public static class SKFunctionMetadataExtensions
{
    /// <summary>
    /// Convert a <see cref="SKFunctionMetadata"/> to an <see cref="OpenAIFunction"/>.
    /// </summary>
    /// <param name="functionView">The <see cref="SKFunctionMetadata"/> object to convert.</param>
    /// <returns>An <see cref="OpenAIFunction"/> object.</returns>
    public static OpenAIFunction ToOpenAIFunction(this SKFunctionMetadata functionView)
    {
        var openAIParams = new List<OpenAIFunctionParameter>();
        foreach (SKParameterMetadata param in functionView.Parameters)
        {
            openAIParams.Add(new OpenAIFunctionParameter
            {
                Name = param.Name,
                Description = param.Description + (string.IsNullOrEmpty(param.DefaultValue) ? string.Empty : $" (default value: {param.DefaultValue})"),
                Type = param.Type?.Name ?? "string",
                IsRequired = param.IsRequired,
                ParameterType = param.ParameterType,
                Schema = param.Schema ?? OpenAIFunction.GetJsonSchema(param.ParameterType, param.Description),
            });
        }

        return new OpenAIFunction
        {
            FunctionName = functionView.Name,
            PluginName = functionView.PluginName ?? "",
            Description = functionView.Description,
            Parameters = openAIParams,
            ReturnParameter = new OpenAIFunctionReturnParameter
            {
                Description = functionView.ReturnParameter.Description,
                Schema = functionView.ReturnParameter.Schema ?? OpenAIFunction.GetJsonSchema(functionView.ReturnParameter.ParameterType, functionView.ReturnParameter.Description),
            }
        };
    }
}
