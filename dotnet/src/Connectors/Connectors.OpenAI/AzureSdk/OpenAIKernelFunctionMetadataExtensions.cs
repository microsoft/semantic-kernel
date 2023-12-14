// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Extensions for <see cref="KernelFunctionMetadata"/> specific to the OpenAI connector.
/// </summary>
public static class OpenAIKernelFunctionMetadataExtensions
{
    /// <summary>
    /// Convert a <see cref="KernelFunctionMetadata"/> to an <see cref="OpenAIFunction"/>.
    /// </summary>
    /// <param name="metadata">The <see cref="KernelFunctionMetadata"/> object to convert.</param>
    /// <returns>An <see cref="OpenAIFunction"/> object.</returns>
    public static OpenAIFunction ToOpenAIFunction(this KernelFunctionMetadata metadata)
    {
        IReadOnlyList<KernelParameterMetadata> metadataParams = metadata.Parameters;

        var openAIParams = new OpenAIFunctionParameter[metadataParams.Count];
        for (int i = 0; i < openAIParams.Length; i++)
        {
            var param = metadataParams[i];
            openAIParams[i] = new OpenAIFunctionParameter(
                param.Name,
                string.IsNullOrEmpty(param.DefaultValue) ? param.Description : $"{param.Description} (default value: {param.DefaultValue})",
                param.IsRequired,
                param.ParameterType,
                param.Schema ?? OpenAIFunction.GetJsonSchema(param.ParameterType, param.Description));
        }

        return new OpenAIFunction(
            metadata.PluginName,
            metadata.Name,
            metadata.Description,
            openAIParams,
            new OpenAIFunctionReturnParameter(
                metadata.ReturnParameter.Description,
                metadata.ReturnParameter.ParameterType,
                metadata.ReturnParameter.Schema ?? OpenAIFunction.GetJsonSchema(metadata.ReturnParameter.ParameterType, metadata.ReturnParameter.Description)));
    }
}
