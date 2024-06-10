// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;

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
                param.Description,
                param.IsRequired,
                param.ParameterType,
                param.Schema,
                param.DefaultValue);
        }

        return new OpenAIFunction(
            metadata.PluginName,
            metadata.Name,
            metadata.Description,
            openAIParams,
            new OpenAIFunctionReturnParameter(
                metadata.ReturnParameter.Description,
                metadata.ReturnParameter.ParameterType,
                metadata.ReturnParameter.Schema));
    }

    /// <summary>
    /// Convert an <see cref="OpenAIFunction"/> to a <see cref="KernelFunctionMetadata"/>.
    /// </summary>
    /// <param name="function">The <see cref="OpenAIFunction"/> object to convert.</param>
    /// <returns>An <see cref="KernelFunctionMetadata"/> object.</returns>
    public static KernelFunctionMetadata ToKernelFunctionMetadata(this OpenAIFunction function)
    {
        return new KernelFunctionMetadata(function.FunctionName)
        {
            PluginName = function.PluginName,
            Description = function.Description,
            Parameters = function.Parameters?.Select(p => new KernelParameterMetadata(p.Name)
            {
                Description = p.Description,
                DefaultValue = p.DefaultValue,
                IsRequired = p.IsRequired,
                ParameterType = p.ParameterType,
                Schema = p.Schema,
            }).ToList() ?? [],
            ReturnParameter = function.ReturnParameter is null ? new() : new KernelReturnParameterMetadata()
            {
                Description = function.ReturnParameter.Description,
                ParameterType = function.ReturnParameter.ParameterType,
                Schema = function.ReturnParameter.Schema,
            },
        };
    }
}
