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

        foreach (KeyValuePair<string, List<FunctionView>> skill in functionsView.NativeFunctions)
        {
            foreach (FunctionView func in skill.Value)
            {
                functionDefinitions.Add(func.ToFunctionDefinition());
            }
        }

        foreach (KeyValuePair<string, List<FunctionView>> skill in functionsView.SemanticFunctions)
        {
            foreach (FunctionView func in skill.Value)
            {
                functionDefinitions.Add(func.ToFunctionDefinition());
            }
        }

        return functionDefinitions;
    }
}
