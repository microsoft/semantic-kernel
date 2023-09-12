// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal static class FunctionViewExtensions
{
    public static FunctionDefinition ToFunctionDefinition(this FunctionView functionView)
    {
        var paramProperties = new Dictionary<string, object>();
        foreach (var param in functionView.Parameters)
        {
            // TODO: what if type is empty?
            paramProperties.Add(
                param.Name,
                new
                {
                    // what are possible values for type? what if unrecognized?
                    type = param.Type?.Name ?? "object",
                    description = param.Description ?? "",
                });
        }

        // TODO: how do I get required parameters?
        // paramProperties.Add("required",

        var functionDefinition = new FunctionDefinition
        {
            Name = string.Join("-", functionView.SkillName, functionView.Name),
            Description = functionView.Description,
            Parameters = BinaryData.FromObjectAsJson(
                new
                {
                    type = "object",
                    properties = paramProperties,
                }),
        };

        // Debug only
        var test = JsonSerializer.Serialize(paramProperties);

        return functionDefinition;
    }
}
