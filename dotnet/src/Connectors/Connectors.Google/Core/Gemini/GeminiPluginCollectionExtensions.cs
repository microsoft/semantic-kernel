﻿// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

/// <summary>
/// Extension methods for <see cref="IReadOnlyKernelPluginCollection"/>.
/// </summary>
internal static class GeminiPluginCollectionExtensions
{
    /// <summary>
    /// Given an <see cref="GeminiFunctionToolCall"/> object, tries to retrieve the corresponding <see cref="KernelFunction"/>
    /// and populate <see cref="KernelArguments"/> with its parameters.
    /// </summary>
    /// <param name="plugins">The plugins.</param>
    /// <param name="functionToolCall">The <see cref="GeminiFunctionToolCall"/> object.</param>
    /// <param name="function">When this method returns, the function that was retrieved
    /// if one with the specified name was found; otherwise, <see langword="null"/></param>
    /// <param name="arguments">When this method returns, the arguments for the function; otherwise, <see langword="null"/></param>
    /// <returns><see langword="true"/> if the function was found; otherwise, <see langword="false"/>.</returns>
    public static bool TryGetFunctionAndArguments(
        this IReadOnlyKernelPluginCollection plugins,
        GeminiFunctionToolCall functionToolCall,
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
                    arguments[parameter.Key] = parameter.Value;
                }
            }

            return true;
        }

        // Function not found in collection
        arguments = null;
        return false;
    }
}
