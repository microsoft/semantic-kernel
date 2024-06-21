// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Azure.AI.OpenAI;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Extension methods for <see cref="IReadOnlyKernelPluginCollection"/>.
/// </summary>
public static class AzureOpenAIPluginCollectionExtensions
{
    /// <summary>
    /// Given an <see cref="AzureOpenAIFunctionToolCall"/> object, tries to retrieve the corresponding <see cref="KernelFunction"/> and populate <see cref="KernelArguments"/> with its parameters.
    /// </summary>
    /// <param name="plugins">The plugins.</param>
    /// <param name="functionToolCall">The <see cref="AzureOpenAIFunctionToolCall"/> object.</param>
    /// <param name="function">When this method returns, the function that was retrieved if one with the specified name was found; otherwise, <see langword="null"/></param>
    /// <param name="arguments">When this method returns, the arguments for the function; otherwise, <see langword="null"/></param>
    /// <returns><see langword="true"/> if the function was found; otherwise, <see langword="false"/>.</returns>
    public static bool TryGetFunctionAndArguments(
        this IReadOnlyKernelPluginCollection plugins,
        ChatCompletionsFunctionToolCall functionToolCall,
        [NotNullWhen(true)] out KernelFunction? function,
        out KernelArguments? arguments) =>
        plugins.TryGetFunctionAndArguments(new AzureOpenAIFunctionToolCall(functionToolCall), out function, out arguments);

    /// <summary>
    /// Given an <see cref="AzureOpenAIFunctionToolCall"/> object, tries to retrieve the corresponding <see cref="KernelFunction"/> and populate <see cref="KernelArguments"/> with its parameters.
    /// </summary>
    /// <param name="plugins">The plugins.</param>
    /// <param name="functionToolCall">The <see cref="AzureOpenAIFunctionToolCall"/> object.</param>
    /// <param name="function">When this method returns, the function that was retrieved if one with the specified name was found; otherwise, <see langword="null"/></param>
    /// <param name="arguments">When this method returns, the arguments for the function; otherwise, <see langword="null"/></param>
    /// <returns><see langword="true"/> if the function was found; otherwise, <see langword="false"/>.</returns>
    public static bool TryGetFunctionAndArguments(
        this IReadOnlyKernelPluginCollection plugins,
        AzureOpenAIFunctionToolCall functionToolCall,
        [NotNullWhen(true)] out KernelFunction? function,
        out KernelArguments? arguments)
    {
        if (plugins.TryGetFunction(functionToolCall.PluginName, functionToolCall.FunctionName, out function))
        {
            // Add parameters to arguments
            arguments = null;
            if (functionToolCall.Arguments is not null)
            {
                arguments = [];
                foreach (var parameter in functionToolCall.Arguments)
                {
                    arguments[parameter.Key] = parameter.Value?.ToString();
                }
            }

            return true;
        }

        // Function not found in collection
        arguments = null;
        return false;
    }
}
