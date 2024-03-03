// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Azure.AI.OpenAI.Assistants;
using Json.More;
using Microsoft.SemanticKernel.Experimental.Agents.Models;

namespace Microsoft.SemanticKernel.Experimental.Agents;

internal static class AssistantsKernelFunctionExtensions
{
    /// <summary>
    /// Produce a fully qualified toolname.
    /// </summary>
    public static string GetQualifiedName(this KernelFunction function, string pluginName)
    {
        return $"{pluginName}-{function.Name}";
    }

    /// <summary>
    /// Convert <see cref="KernelFunction"/> to an OpenAI tool model.
    /// </summary>
    /// <param name="function">The source function</param>
    /// <param name="pluginName">The plugin name</param>
    /// <returns>An OpenAI tool model</returns>
    public static ToolModel ToToolModel(this KernelFunction function, string pluginName)
    {
        var metadata = function.Metadata;
        var required = new List<string>(metadata.Parameters.Count);
        var properties =
            metadata.Parameters.ToDictionary(
                p => p.Name,
                p =>
                {
                    if (p.IsRequired)
                    {
                        required.Add(p.Name);
                    }

                    return
                        new OpenAIParameter
                        {
                            Type = ConvertType(p.ParameterType),
                            Description = p.Description,
                        };
                });

        var payload =
            new ToolModel
            {
                Type = "function",
                Function =
                    new()
                    {
                        Name = function.GetQualifiedName(pluginName),
                        Description = function.Description,
                        Parameters =
                                new OpenAIParameters
                                {
                                    Properties = properties,
                                    Required = required,
                                },
                    },
            };

        return payload;
    }

    /// <summary>
    /// Convert <see cref="KernelFunction"/> to an OpenAI tool model.
    /// </summary>
    /// <param name="function">The source function</param>
    /// <param name="pluginName">The plugin name</param>
    /// <returns>An OpenAI tool definition</returns>
    public static ToolDefinition ToToolDefinition(this KernelFunction function, string pluginName)
    {
        var metadata = function.Metadata;
        if (metadata.Parameters.Count > 0)
        {
            var required = new List<string>(metadata.Parameters.Count);
            var parameters =
                metadata.Parameters.ToDictionary(
                    p => p.Name,
                    p =>
                    {
                        if (p.IsRequired)
                        {
                            required.Add(p.Name);
                        }

                        return
                            new
                            {
                                type = ConvertType(p.ParameterType),
                                description = p.Description,
                            };
                    });

            var spec =
                new
                {
                    type = "object",
                    properties = parameters,
                    required,
                };

            return new FunctionToolDefinition(function.GetQualifiedName(pluginName), function.Description, BinaryData.FromObjectAsJson(spec));
        }

        return new FunctionToolDefinition(function.GetQualifiedName(pluginName), function.Description);
    }

    private static string ConvertType(Type? type)
    {
        if (type == null || type == typeof(string))
        {
            return "string";
        }

        if (type.IsNumber())
        {
            return "number";
        }

        if (type.IsEnum)
        {
            return "enum";
        }

        return type.Name;
    }
}
