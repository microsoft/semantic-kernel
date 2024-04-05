// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Anthropic;

namespace SemanticKernel.Connectors.Anthropic.UnitTests;

/// <summary>
/// Extensions for <see cref="KernelFunctionMetadata"/> specific to the Claude connector.
/// </summary>
public static class ClaudeKernelFunctionMetadataExtensions
{
    /// <summary>
    /// Convert a <see cref="KernelFunctionMetadata"/> to an <see cref="ClaudeFunction"/>.
    /// </summary>
    /// <param name="metadata">The <see cref="KernelFunctionMetadata"/> object to convert.</param>
    /// <returns>An <see cref="ClaudeFunction"/> object.</returns>
    public static ClaudeFunction ToClaudeFunction(this KernelFunctionMetadata metadata)
    {
        IReadOnlyList<KernelParameterMetadata> metadataParams = metadata.Parameters;

        var openAIParams = new ClaudeFunctionParameter[metadataParams.Count];
        for (int i = 0; i < openAIParams.Length; i++)
        {
            var param = metadataParams[i];

            openAIParams[i] = new ClaudeFunctionParameter(
                param.Name,
                GetDescription(param),
                param.IsRequired,
                param.ParameterType,
                param.Schema);
        }

        return new ClaudeFunction(
            metadata.PluginName,
            metadata.Name,
            metadata.Description,
            openAIParams,
            new ClaudeFunctionReturnParameter(
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
