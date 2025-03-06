// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;

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
        JsonSchemaFunctionParameters parameterSpec = new();
        List<string> required = new(metadata.Parameters.Count);

        foreach (var parameter in metadata.Parameters)
        {
            if (parameter.IsRequired)
            {
                parameterSpec.Required.Add(parameter.Name);
            }

            if (parameter.Schema is null)
            {
                throw new KernelException($"Unsupported function parameter: {metadata.PluginName ?? "*"}.{metadata.Name}.{parameter.Name}");
            }

            parameterSpec.Properties.Add(parameter.Name, parameter.Schema);
        }

        return BinaryData.FromObjectAsJson(parameterSpec);
    }
}
