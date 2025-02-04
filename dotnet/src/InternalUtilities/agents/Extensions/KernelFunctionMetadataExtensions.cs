// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel.Agents;

internal static class KernelFunctionMetadataExtensions
{
    /// <summary>
    /// Transform the function parameter metadata into a binary parameter spec.
    /// </summary>
    /// <param name="metadata">The function meta-data</param>
    /// <returns>The parameter spec as <see cref="BinaryData"/></returns>
    internal static BinaryData CreateParameterSpec(this KernelFunctionMetadata metadata)
    {
        List<string> required = new(metadata.Parameters.Count);
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

        return BinaryData.FromObjectAsJson(spec);
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
