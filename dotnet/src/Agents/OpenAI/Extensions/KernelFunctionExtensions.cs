// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

internal static class KernelFunctionExtensions
{
    /// <summary>
    /// Convert <see cref="KernelFunction"/> to an OpenAI tool model.
    /// </summary>
    /// <param name="function">The source function</param>
    /// <param name="pluginName">The plugin name</param>
    /// <returns>An OpenAI tool definition</returns>
    public static FunctionToolDefinition ToToolDefinition(this KernelFunction function, string pluginName)
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

            return new FunctionToolDefinition(FunctionName.ToFullyQualifiedName(function.Name, pluginName))
            {
                Description = function.Description,
                Parameters = BinaryData.FromObjectAsJson(spec)
            };
        }

        return new FunctionToolDefinition(FunctionName.ToFullyQualifiedName(function.Name, pluginName))
        {
            Description = function.Description
        };
    }

    private static string ConvertType(Type? type)
    {
        if (type is null || type == typeof(string))
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

        if (type == typeof(DateTime) || type == typeof(DateTimeOffset))
        {
            return "date-time";
        }

        return Type.GetTypeCode(type) switch
        {
            TypeCode.SByte or TypeCode.Byte or
            TypeCode.Int16 or TypeCode.UInt16 or
            TypeCode.Int32 or TypeCode.UInt32 or
            TypeCode.Int64 or TypeCode.UInt64 or
            TypeCode.Single or TypeCode.Double or TypeCode.Decimal => "number",

            _ => "object",
        };
    }
}
