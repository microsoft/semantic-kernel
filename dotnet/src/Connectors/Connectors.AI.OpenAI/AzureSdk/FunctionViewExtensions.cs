// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal static class FunctionViewExtensions
{
    public static FunctionDefinition ToFunctionDefinition(this FunctionView functionView)
    {
        var requiredParams = new List<string>();

        var paramProperties = new Dictionary<string, object>();
        foreach (var param in functionView.Parameters)
        {
            paramProperties.Add(
                param.Name,
                new
                {
                    type = param.Type?.Name ?? "string",
                    description = param.Description ?? "",
                });

            if (param.IsRequired)
            {
                requiredParams.Add(param.Name);
            }
        }

        var functionDefinition = new FunctionDefinition
        {
            Name = (functionView.SkillName.IsNullOrEmpty() ? functionView.Name : string.Join("-", functionView.SkillName, functionView.Name)),
            Description = functionView.Description,
            Parameters = BinaryData.FromObjectAsJson(
                new
                {
                    type = "object",
                    properties = paramProperties,
                    required = requiredParams,
                }),
        };

        return functionDefinition;
    }
}
