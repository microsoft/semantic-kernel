// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.OpenApi.Models;
using Microsoft.OpenApi.Services;

namespace Microsoft.SemanticKernel.Plugins.OpenApi.Extensions;

/// <summary>
/// Copilot Agent Plugin OpenAPI document visitor that:
///  * Normalizes the operation IDs by replacing dots with underscores. So that the operation IDs can be used as function names in semantic kernel.
///  * Truncates the description to the maximum allowed length.
///  * Removes properties and parameters with the same name.
/// </summary>
internal sealed class CopilotAgentPluginOpenApiDocumentVisitor : OpenApiVisitorBase
{
    private const int MaximumDescription = 1000;

    public override void Visit(OpenApiOperation operation)
    {
        NormalizeOperationId(operation);

        TruncateOperationDescription(operation);

        RemoveDuplicateOperationProperties(operation);
    }

    private static void NormalizeOperationId(OpenApiOperation operation)
    {
        if (operation?.OperationId is null)
        {
            return;
        }
        operation.OperationId = operation.OperationId.Replace('.', '_');
    }

    private static void TruncateOperationDescription(OpenApiOperation operation)
    {
        if (operation.Description?.Length > MaximumDescription)
        {
            operation.Description = operation.Description.Substring(0, MaximumDescription);
        }
    }

    private static void RemoveDuplicateOperationProperties(OpenApiOperation operation)
    {
        HashSet<string> visitedNames = [];

        // Lookup for duplicate parameters and remove them
        for (int index = 0; index < operation.Parameters.Count;)
        {
            var parameter = operation.Parameters[index];
            if (visitedNames.Contains(parameter.Name))
            {
                operation.Parameters.Remove(parameter);
                continue;
            }

            visitedNames.Add(parameter.Name);
            index++;
        }

        // Lookup for duplicate properties in request body and remove them
        if (operation.RequestBody is not null)
        {
            foreach (var content in operation.RequestBody.Content)
            {
                RemoveProperty(content.Value.Schema, visitedNames);
            }
        }
    }

    private static void RemoveProperty(OpenApiSchema schema, HashSet<string> visitedNames)
    {
        for (int index = 0; index < schema.Properties.Count;)
        {
            var property = schema.Properties.ElementAt(index);
            if (visitedNames.Contains(property.Key))
            {
                schema.Properties.Remove(property.Key);
                continue;
            }

            visitedNames.Add(property.Key);
            RemoveProperty(property.Value, visitedNames);
            index++;
        }
    }
}
