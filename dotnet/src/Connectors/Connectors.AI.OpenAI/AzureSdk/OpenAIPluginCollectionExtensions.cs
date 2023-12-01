// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI;

/// <summary>
/// Extension methods for <see cref="IReadOnlyKernelPluginCollection"/>.
/// </summary>
public static class OpenAIPluginCollectionExtensions
{
    /// <summary>
    /// Given an <see cref="OpenAIFunctionResponse"/> object, tries to retrieve the corresponding <see cref="KernelFunction"/> and populate <see cref="KernelArguments"/> with its parameters.
    /// </summary>
    /// <param name="plugins">The plugins.</param>
    /// <param name="response">The <see cref="OpenAIFunctionResponse"/> object.</param>
    /// <param name="availableFunction">When this method returns, the function that was retrieved if one with the specified name was found; otherwise, <see langword="null"/></param>
    /// <param name="arguments">When this method returns, the arguments for the function; otherwise, <see langword="null"/></param>
    /// <returns><see langword="true"/> if the function was found; otherwise, <see langword="false"/>.</returns>
    public static bool TryGetFunctionAndArguments(
        this IReadOnlyKernelPluginCollection plugins,
        OpenAIFunctionResponse response,
        [NotNullWhen(true)] out KernelFunction? availableFunction,
        [NotNullWhen(true)] out KernelArguments? arguments)
    {
        availableFunction = null;
        arguments = null;

        if (!plugins.TryGetFunction(response.PluginName, response.FunctionName, out availableFunction))
        {
            // Function not found in collection
            return false;
        }

        // Add parameters to arguments
        arguments = new KernelArguments();
        foreach (var parameter in response.Parameters)
        {
            arguments[parameter.Key] = parameter.Value.ToString();
        }

        return true;
    }
}
