// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.Google.Extensions;

/// <summary>
/// Extensions for <see cref="KernelFunctionMetadata"/> specific to the Gemini connector.
/// </summary>
public static class GeminiKernelFunctionMetadataExtensions
{
    /// <summary>
    /// Convert a <see cref="KernelFunctionMetadata"/> to an <see cref="GeminiFunction"/>.
    /// </summary>
    /// <param name="metadata">The <see cref="KernelFunctionMetadata"/> object to convert.</param>
    /// <returns>An <see cref="GeminiFunction"/> object.</returns>
    public static GeminiFunction ToGeminiFunction(this KernelFunctionMetadata metadata)
    {
        IReadOnlyList<KernelParameterMetadata> metadataParams = metadata.Parameters;

        var openAIParams = new GeminiFunctionParameter[metadataParams.Count];
        for (int i = 0; i < openAIParams.Length; i++)
        {
            var param = metadataParams[i];

            openAIParams[i] = new GeminiFunctionParameter(
                param.Name,
                GetDescription(param),
                param.IsRequired,
                param.ParameterType,
                param.Schema);
        }

        return new GeminiFunction(
            metadata.PluginName,
            metadata.Name,
            metadata.Description,
            openAIParams,
            new GeminiFunctionReturnParameter(
                metadata.ReturnParameter.Description,
                metadata.ReturnParameter.ParameterType,
                metadata.ReturnParameter.Schema));

        static string GetDescription(KernelParameterMetadata param)
        {
            string? stringValue = InternalTypeConverter.ConvertToString(param.DefaultValue);
            return !string.IsNullOrEmpty(stringValue) ? $"{param.Description} (default value: {stringValue})" : param.Description;
        }
    }
}
