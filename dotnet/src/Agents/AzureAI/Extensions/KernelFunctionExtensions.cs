// Copyright (c) Microsoft. All rights reserved.
using System;
using Azure.AI.Agents.Persistent;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Extensions for <see cref="KernelFunction"/> to support Azure AI specific operations.
/// </summary>
public static class KernelFunctionExtensions
{
    /// <summary>
    /// Convert <see cref="KernelFunction"/> to an OpenAI tool model.
    /// </summary>
    /// <param name="function">The source function</param>
    /// <param name="pluginName">The plugin name</param>
    /// <returns>An OpenAI tool definition</returns>
    public static FunctionToolDefinition ToToolDefinition(this KernelFunction function, string pluginName)
    {
        if (function.Metadata.Parameters.Count > 0)
        {
            BinaryData parameterData = function.Metadata.CreateParameterSpec();

            return new FunctionToolDefinition(FunctionName.ToFullyQualifiedName(function.Name, pluginName), function.Description, parameterData);
        }

        return new FunctionToolDefinition(FunctionName.ToFullyQualifiedName(function.Name, pluginName), function.Description);
    }
}
