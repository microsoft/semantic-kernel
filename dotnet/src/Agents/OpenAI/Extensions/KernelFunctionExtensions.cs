// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using Azure.AI.OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI.Extensions;

internal static class KernelFunctionExtensions
{
    /// <summary>
    /// Convert <see cref="KernelFunction"/> to an OpenAI tool model.
    /// </summary>
    /// <param name="function">The source function</param>
    /// <param name="pluginName">The plugin name</param>
    /// <param name="delimiter">The delimiter character</param>
    /// <returns>An OpenAI tool definition</returns>
    public static ToolDefinition ToToolDefinition(this KernelFunction function, string pluginName, char delimiter)
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

            return new FunctionToolDefinition(function.GetQualifiedName(pluginName, delimiter), function.Description, BinaryData.FromObjectAsJson(spec));
        }

        return new FunctionToolDefinition(function.GetQualifiedName(pluginName, delimiter), function.Description);
    }

    private static string ConvertType(Type? type)
    {
        if (type == null || type == typeof(string))
        {
            return "string";
        }

        if (type == typeof(bool))
        {
            return "boolean";
        }

        if (type.IsEnum)
        {
            return "enum";
        }

        if (type.IsArray)
        {
            return "array";
        }

        switch (Type.GetTypeCode(type))
        {
            case TypeCode.SByte:
            case TypeCode.Byte:
            case TypeCode.Int16:
            case TypeCode.UInt16:
            case TypeCode.Int32:
            case TypeCode.UInt32:
            case TypeCode.Int64:
            case TypeCode.UInt64:
            case TypeCode.Single:
            case TypeCode.Double:
            case TypeCode.Decimal:
                return "number";
        }

        return "object";
    }
    /// <summary>
    /// Produce a fully qualified toolname.
    /// </summary>
    public static string GetQualifiedName(this KernelFunction function, string pluginName, char delimiter)
    {
        return $"{pluginName}{delimiter}{function.Name}";
    }
}
