// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;
using System.Collections.Generic;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal static class FunctionsViewExtensions
{
    public static IList<FunctionDefinition> ToFunctionDefinitions(this FunctionsView functionsView)
    {
        var functionDefinitions = new List<FunctionDefinition>();

        ConcurrentDictionary<string, List<FunctionView>> nativeFunctions = functionsView.NativeFunctions;
        ConcurrentDictionary<string, List<FunctionView>> semanticFunctions = functionsView.SemanticFunctions;

        foreach (KeyValuePair<string, List<FunctionView>> skill in nativeFunctions)
        {
            foreach (FunctionView func in skill.Value)
            {
                functionDefinitions.Add(func.ToFunctionDefinition());
            }
        }

        foreach (KeyValuePair<string, List<FunctionView>> skill in semanticFunctions)
        {
            foreach (FunctionView func in skill.Value)
            {
                functionDefinitions.Add(func.ToFunctionDefinition());
            }
        }

        return functionDefinitions;
    }
}
