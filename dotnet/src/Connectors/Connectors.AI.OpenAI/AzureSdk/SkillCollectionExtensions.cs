// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Extension methods for <see cref="IReadOnlySkillCollection"/>.
/// </summary>
public static class SkillCollectionExtensions
{
    /// <summary>
    /// Given an <see cref="OpenAIFunctionResponse"/> object, tries to retrieve the corresponding <see cref="ISKFunction"/> and populate <see cref="ContextVariables"/> with its parameters.
    /// </summary>
    /// <param name="skills">The skill collection.</param>
    /// <param name="response">The <see cref="OpenAIFunctionResponse"/> object.</param>
    /// <param name="availableFunction">When this method returns, the function that was retrieved if one with the specified name was found; otherwise, <see langword="null"/></param>
    /// <param name="availableContext">When this method returns, the context variables containing parameters for the function; otherwise, <see langword="null"/></param>
    /// <returns><see langword="true"/> if the function was found; otherwise, <see langword="false"/>.</returns>
    public static bool TryGetFunctionAndContext(
        this IReadOnlySkillCollection skills,
        OpenAIFunctionResponse response,
        [NotNullWhen(true)] out ISKFunction? availableFunction,
        [NotNullWhen(true)] out ContextVariables? availableContext)
    {
        availableFunction = null;
        availableContext = null;

        if (!skills.TryGetFunction(response.PluginName, response.FunctionName, out availableFunction))
        {
            if (!skills.TryGetFunction(response.FunctionName, out availableFunction))
            {
                // Function not found in skill collection
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
