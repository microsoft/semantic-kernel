// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Amazon.BedrockAgent.Model;
using Amazon.BedrockAgentRuntime.Model;

namespace Microsoft.SemanticKernel.Agents.Bedrock.Extensions;

/// <summary>
/// Extensions associated with the status of a <see cref="BedrockAgent"/>.
/// </summary>
internal static class BedrockFunctionSchemaExtensions
{
    public static KernelArguments FromFunctionParameters(this List<FunctionParameter> parameters, KernelArguments? arguments)
    {
        KernelArguments kernelArguments = arguments ?? [];
        foreach (var parameter in parameters)
        {
            kernelArguments.Add(parameter.Name, parameter.Value);
        }

        return kernelArguments;
    }

    public static Amazon.BedrockAgent.Model.FunctionSchema ToFunctionSchema(this Kernel kernel)
    {
        var plugins = kernel.Plugins;
        List<Function> functions = [];
        foreach (var plugin in plugins)
        {
            foreach (KernelFunction function in plugin)
            {
                functions.Add(new Function
                {
                    Name = function.Name,
                    Description = function.Description,
                    Parameters = function.Metadata.Parameters.CreateParameterSpec(),
                    // This field controls whether user confirmation is required to invoke the function.
                    // If this is set to "ENABLED", the user will be prompted to confirm the function invocation.
                    // Only after the user confirms, the function call request will be issued by the agent.
                    // If the user denies the confirmation, the agent will act as if the function does not exist.
                    // Currently, we do not support this feature, so we set it to "DISABLED".
                    RequireConfirmation = Amazon.BedrockAgent.RequireConfirmation.DISABLED,
                });
            }
        }

        return new Amazon.BedrockAgent.Model.FunctionSchema
        {
            Functions = functions,
        };
    }

    private static Dictionary<string, Amazon.BedrockAgent.Model.ParameterDetail> CreateParameterSpec(
        this IReadOnlyList<KernelParameterMetadata> parameters)
    {
        Dictionary<string, Amazon.BedrockAgent.Model.ParameterDetail> parameterSpec = [];
        foreach (var parameter in parameters)
        {
            parameterSpec.Add(parameter.Name, new Amazon.BedrockAgent.Model.ParameterDetail
            {
                Description = parameter.Description,
                Required = parameter.IsRequired,
                Type = parameter.ParameterType.ToAmazonType(),
            });
        }

        return parameterSpec;
    }

    private static Amazon.BedrockAgent.Type ToAmazonType(this System.Type? parameterType)
    {
        var typeString = parameterType?.GetFriendlyTypeName();
        return typeString switch
        {
            "String" => Amazon.BedrockAgent.Type.String,
            "Boolean" => Amazon.BedrockAgent.Type.Boolean,
            "Int16" => Amazon.BedrockAgent.Type.Integer,
            "UInt16" => Amazon.BedrockAgent.Type.Integer,
            "Int32" => Amazon.BedrockAgent.Type.Integer,
            "UInt32" => Amazon.BedrockAgent.Type.Integer,
            "Int64" => Amazon.BedrockAgent.Type.Integer,
            "UInt64" => Amazon.BedrockAgent.Type.Integer,
            "Single" => Amazon.BedrockAgent.Type.Number,
            "Double" => Amazon.BedrockAgent.Type.Number,
            "Decimal" => Amazon.BedrockAgent.Type.Number,
            "String[]" => Amazon.BedrockAgent.Type.Array,
            "Boolean[]" => Amazon.BedrockAgent.Type.Array,
            "Int16[]" => Amazon.BedrockAgent.Type.Array,
            "UInt16[]" => Amazon.BedrockAgent.Type.Array,
            "Int32[]" => Amazon.BedrockAgent.Type.Array,
            "UInt32[]" => Amazon.BedrockAgent.Type.Array,
            "Int64[]" => Amazon.BedrockAgent.Type.Array,
            "UInt64[]" => Amazon.BedrockAgent.Type.Array,
            "Single[]" => Amazon.BedrockAgent.Type.Array,
            "Double[]" => Amazon.BedrockAgent.Type.Array,
            "Decimal[]" => Amazon.BedrockAgent.Type.Array,
            _ => throw new ArgumentException($"Unsupported parameter type: {typeString}"),
        };
    }
}
