// Copyright (c) Microsoft. All rights reserved.
using System;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Extensions for <see cref="KernelFunction"/> to support OpenAI specific operations.
/// </summary>
public static class KernelFunctionExtensions
{
    /// <summary>
    /// Convert <see cref="KernelFunction"/> to an OpenAI tool model.
    /// </summary>
    /// <param name="function">The source function</param>
    /// <param name="pluginName">The plugin name</param>
    /// <returns>An OpenAI tool definition</returns>
    public static FunctionToolDefinition ToToolDefinition(this KernelFunction function, string? pluginName = null)
    {
        if (function.Metadata.Parameters.Count > 0)
        {
            BinaryData parameterData = function.Metadata.CreateParameterSpec();

            return new FunctionToolDefinition(FunctionName.ToFullyQualifiedName(function.Name, pluginName ?? function.PluginName))
            {
                Description = function.Description,
                Parameters = parameterData,
            };
        }

        return new FunctionToolDefinition(FunctionName.ToFullyQualifiedName(function.Name, pluginName ?? function.PluginName))
        {
            Description = function.Description
        };
    }
}
