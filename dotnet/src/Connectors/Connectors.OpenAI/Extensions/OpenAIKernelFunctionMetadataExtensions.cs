// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Extensions for <see cref="KernelFunctionMetadata"/> specific to the OpenAI connector.
/// </summary>
public static class OpenAIKernelFunctionMetadataExtensions
{
    /// <summary>
    /// Convert a <see cref="KernelFunctionMetadata"/> to an <see cref="OpenAIFunctionParameter"/>.
    /// </summary>
    /// <param name="metadata">The <see cref="KernelFunctionMetadata"/> object to convert.</param>
    /// <param name="allowStrictSchemaAdherence">Whether to allow strict adherence to the schema.</param>
    /// <returns>An <see cref="OpenAIFunction"/> object.</returns>
    public static OpenAIFunction ToOpenAIFunction(this KernelFunctionMetadata metadata, bool? allowStrictSchemaAdherence = null)
    {
        IReadOnlyList<KernelParameterMetadata> metadataParams = metadata.Parameters;

        var openAIParams = new OpenAIFunctionParameter[metadataParams.Count];
        for (int i = 0; i < openAIParams.Length; i++)
        {
            var param = metadataParams[i];

            openAIParams[i] = new OpenAIFunctionParameter(
                param.Name,
                GetDescription(param),
                param.IsRequired,
                param.ParameterType,
                param.Schema);
        }

        return new OpenAIFunction(
            metadata.PluginName,
            metadata.Name,
            metadata.Description,
            openAIParams,
            new OpenAIFunctionReturnParameter(
                metadata.ReturnParameter.Description,
                metadata.ReturnParameter.ParameterType,
                metadata.ReturnParameter.Schema),
            metadata.Strict == true && allowStrictSchemaAdherence != false);

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
