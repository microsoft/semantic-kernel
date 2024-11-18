// Copyright (c) Microsoft. All rights reserved.

using Microsoft.OpenApi.Models;
using Microsoft.OpenApi.Services;

namespace Microsoft.SemanticKernel.Plugins.OpenApi.Extensions;

/// <summary>
/// An OpenAPI visitor that normalizes the operation IDs by replacing dots with underscores.
/// So that the operation IDs can be used as function names in semantic kernel.
/// </summary>
internal sealed class OperationIdNormalizationOpenApiVisitor : OpenApiVisitorBase
{
    public override void Visit(OpenApiOperation operation)
    {
        if (operation is null || operation.OperationId is null)
        {
            return;
        }
        operation.OperationId = operation.OperationId.Replace('.', '_');
    }
}
