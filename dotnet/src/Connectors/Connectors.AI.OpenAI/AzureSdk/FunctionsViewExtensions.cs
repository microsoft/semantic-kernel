// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Extensions for <see cref="FunctionsView"/> specific to the OpenAI connector.
/// </summary>
public static class FunctionsViewExtensions
{
    /// <summary>
    /// Convert a <see cref="FunctionsView"/> object to a list of <see cref="OpenAIFunction"/> objects.
    /// </summary>
    /// <param name="functionsView">The <see cref="FunctionsView"/> object to convert.</param>
    /// <returns>List of <see cref="OpenAIFunction"/> objects.</returns>
    public static IList<OpenAIFunction> ToOpenAIFunctions(this FunctionsView functionsView)
    {
        var openAIFunctions = new List<OpenAIFunction>();

        foreach (KeyValuePair<string, List<FunctionView>> skill in functionsView.NativeFunctions)
        {
            foreach (FunctionView func in skill.Value)
            {
                openAIFunctions.Add(func.ToOpenAIFunction());
            }
        }

        foreach (KeyValuePair<string, List<FunctionView>> skill in functionsView.SemanticFunctions)
        {
            foreach (FunctionView func in skill.Value)
            {
                openAIFunctions.Add(func.ToOpenAIFunction());
            }
        }

        return openAIFunctions;
    }
}
