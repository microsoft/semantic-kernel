// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Extensions for <see cref="KernelFunctionMetadata"/> specific to the OpenAI connector.
/// </summary>
public static class KernelFunctionMetadataExtensions
{
    /// <summary>
    /// Convert a <see cref="KernelFunctionMetadata"/> to an <see cref="OpenAIFunction"/>.
    /// </summary>
    /// <param name="metadata">The <see cref="KernelFunctionMetadata"/> object to convert.</param>
    /// <returns>An <see cref="OpenAIFunction"/> object.</returns>
    public static OpenAIFunction ToOpenAIFunction(this KernelFunctionMetadata metadata)
    {
        var openAIParams = new List<OpenAIFunctionParameter>();
        foreach (KernelParameterMetadata param in metadata.Parameters)
        {
            openAIParams.Add(new OpenAIFunctionParameter
            {
                Name = param.Name,
                Description = string.IsNullOrEmpty(param.DefaultValue) ? param.Description : $"{param.Description} (default value: {param.DefaultValue})",
                IsRequired = param.IsRequired,
                ParameterType = param.ParameterType,
                Schema = param.Schema ?? OpenAIFunction.GetJsonSchema(param.ParameterType, param.Description),
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
