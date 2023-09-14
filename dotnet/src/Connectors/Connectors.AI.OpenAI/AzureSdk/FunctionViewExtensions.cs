// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal static class FunctionViewExtensions
{
    public static FunctionDefinition ToFunctionDefinition(this FunctionView functionView)
    {
        var requiredParams = new List<string>();

        var paramProperties = new Dictionary<string, object>();
        foreach (var param in functionView.Parameters)
        {
            // TODO: what if type is empty?
            paramProperties.Add(
                param.Name,
                new
                {
                    // what are possible values for type? what if unrecognized?
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
            Name = string.Join("-", functionView.SkillName, functionView.Name),
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
