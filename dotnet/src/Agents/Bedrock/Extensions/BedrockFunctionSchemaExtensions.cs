// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using AmazonBedrockAgentModel = Amazon.BedrockAgent.Model;
using AmazonBedrockAgentRuntimeModel = Amazon.BedrockAgentRuntime.Model;

namespace Microsoft.SemanticKernel.Agents.Bedrock.Extensions;

/// <summary>
/// Extensions associated with the status of a <see cref="BedrockAgent"/>.
/// </summary>
internal static class BedrockFunctionSchemaExtensions
{
    public static KernelArguments FromFunctionParameters(this List<AmazonBedrockAgentRuntimeModel.FunctionParameter> parameters, KernelArguments? arguments)
    {
        KernelArguments kernelArguments = arguments ?? [];
        foreach (var parameter in parameters)
        {
            kernelArguments.Add(parameter.Name, parameter.Value);
        }

        return kernelArguments;
    }

    public static AmazonBedrockAgentModel.FunctionSchema ToFunctionSchema(this Kernel kernel)
    {
        var plugins = kernel.Plugins;
        List<AmazonBedrockAgentModel.Function> functions = [];
        foreach (var plugin in plugins)
        {
            foreach (KernelFunction function in plugin)
            {
                functions.Add(new AmazonBedrockAgentModel.Function
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

        return new AmazonBedrockAgentModel.FunctionSchema
        {
            Functions = functions,
        };
    }

    private static Dictionary<string, AmazonBedrockAgentModel.ParameterDetail> CreateParameterSpec(
        this IReadOnlyList<KernelParameterMetadata> parameters)
    {
        Dictionary<string, AmazonBedrockAgentModel.ParameterDetail> parameterSpec = [];
        foreach (var parameter in parameters)
        {
            parameterSpec.Add(parameter.Name, new AmazonBedrockAgentModel.ParameterDetail
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
            // TODO: Add support for array type.
            _ => throw new ArgumentException($"Unsupported parameter type: {typeString}"),
        };
    }
}
