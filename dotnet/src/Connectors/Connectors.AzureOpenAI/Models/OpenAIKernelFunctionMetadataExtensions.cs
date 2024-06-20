// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Extensions for <see cref="KernelFunctionMetadata"/> specific to the OpenAI connector.
/// </summary>
public static class OpenAIKernelFunctionMetadataExtensions
{
    /// <summary>
    /// Convert a <see cref="KernelFunctionMetadata"/> to an <see cref="AzureOpenAIFunction"/>.
    /// </summary>
    /// <param name="metadata">The <see cref="KernelFunctionMetadata"/> object to convert.</param>
    /// <returns>An <see cref="AzureOpenAIFunction"/> object.</returns>
    public static AzureOpenAIFunction ToAzureOpenAIFunction(this KernelFunctionMetadata metadata)
    {
        IReadOnlyList<KernelParameterMetadata> metadataParams = metadata.Parameters;

        var openAIParams = new AzureOpenAIFunctionParameter[metadataParams.Count];
        for (int i = 0; i < openAIParams.Length; i++)
        {
            var param = metadataParams[i];

            openAIParams[i] = new AzureOpenAIFunctionParameter(
                param.Name,
                GetDescription(param),
                param.IsRequired,
                param.ParameterType,
                param.Schema);
        }

        return new AzureOpenAIFunction(
            metadata.PluginName,
            metadata.Name,
            metadata.Description,
            openAIParams,
            new AzureOpenAIFunctionReturnParameter(
                metadata.ReturnParameter.Description,
                metadata.ReturnParameter.ParameterType,
                metadata.ReturnParameter.Schema));

        static string GetDescription(KernelParameterMetadata param)
        {
            if (InternalTypeConverter.ConvertToString(param.DefaultValue) is string stringValue && !string.IsNullOrEmpty(stringValue))
            {
                return $"{param.Description} (default value: {stringValue})";
            }

            return param.Description;
        }
    }
}
