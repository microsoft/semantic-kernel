// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Extensions for <see cref="FunctionView"/> specific to the OpenAI connector.
/// </summary>
public static class FunctionViewExtensions
{
    /// <summary>
    /// Convert a <see cref="FunctionView"/> to an <see cref="OpenAIFunction"/>.
    /// </summary>
    /// <param name="functionView">The <see cref="FunctionView"/> object to convert.</param>
    /// <returns>An <see cref="OpenAIFunction"/> object.</returns>
    public static OpenAIFunction ToOpenAIFunction(this FunctionView functionView)
    {
        var openAIParams = new List<OpenAIFunctionParameter>();
        foreach (ParameterView param in functionView.Parameters)
        {
            openAIParams.Add(new OpenAIFunctionParameter
            {
                Name = param.Name,
                Description = param.Description ?? string.Empty,
                Type = param.Type?.Name ?? "string",
                IsRequired = param.IsRequired,
            });
        }

        return new OpenAIFunction
        {
            Name = (functionView.SkillName.IsNullOrEmpty() ? functionView.Name : string.Join("-", functionView.SkillName, functionView.Name)),
            Description = functionView.Description,
            Parameters = openAIParams,
        };
    }
}
