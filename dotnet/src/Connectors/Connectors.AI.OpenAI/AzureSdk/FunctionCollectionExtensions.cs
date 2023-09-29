// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Extension methods for <see cref="IReadOnlyFunctionCollection"/>.
/// </summary>
public static class FunctionCollectionExtensions
{
    /// <summary>
    /// Given an <see cref="OpenAIFunctionResponse"/> object, tries to retrieve the corresponding <see cref="ISKFunction"/> and populate <see cref="ContextVariables"/> with its parameters.
    /// </summary>
    /// <param name="functionCollection">The SK function collection.</param>
    /// <param name="response">The <see cref="OpenAIFunctionResponse"/> object.</param>
    /// <param name="availableFunction">When this method returns, the function that was retrieved if one with the specified name was found; otherwise, <see langword="null"/></param>
    /// <param name="availableContext">When this method returns, the context variables containing parameters for the function; otherwise, <see langword="null"/></param>
    /// <returns><see langword="true"/> if the function was found; otherwise, <see langword="false"/>.</returns>
    public static bool TryGetFunctionAndContext(
        this IReadOnlyFunctionCollection functionCollection,
        OpenAIFunctionResponse response,
        [NotNullWhen(true)] out ISKFunction? availableFunction,
        [NotNullWhen(true)] out ContextVariables? availableContext)
    {
        availableFunction = null;
        availableContext = null;

        if (!functionCollection.TryGetFunction(response.PluginName, response.FunctionName, out availableFunction))
        {
            if (!functionCollection.TryGetFunction(response.FunctionName, out availableFunction))
            {
                // Function not found in collection
                return false;
            }
        }

        // Add parameters to context variables
        availableContext = new ContextVariables();
        foreach (var parameter in response.Parameters)
        {
            availableContext.Set(parameter.Key, parameter.Value.ToString());
        }

        return true;
    }
}
